#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Niccolò Bonacchi
# @Date:   2018-06-08 11:04:05
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from packaging import version

# BEGIN CONSTANT DEFINITION
IBLRIG_ROOT_PATH = Path.cwd()

if sys.platform not in ["Windows", "windows", "win32"]:
    print("\nWARNING: Unsupported OS\nInstallation might not work!")
# END CONSTANT DEFINITION


def get_env_folder(env_name: str = "iblenv") -> str:
    """get_env_folder Return conda folder of [env_name] environment

    :param env_name: name of conda environment to look for, defaults to 'iblenv'
    :type env_name: str, optional
    :return: folder path of conda environment
    :rtype: str
    """
    all_envs = subprocess.check_output(["conda", "env", "list", "--json"])
    all_envs = json.loads(all_envs.decode("utf-8"))
    pat = re.compile(f"^.+{env_name}$")
    env = [x for x in all_envs["envs"] if pat.match(x)]
    env = env[0] if env else None
    return env


def get_env_python(env_name: str = "iblenv", rpip=False):
    env = get_env_folder(env_name=env_name)
    if sys.platform in ["Windows", "windows", "win32"]:
        pip = os.path.join(env, "Scripts", "pip.exe")
        python = os.path.join(env, "python.exe")
    else:
        pip = os.path.join(env, "bin", "pip")
        python = os.path.join(env, "bin", "python")

    return python if not rpip else pip


def check_dependencies():
    # Check if Git and conda are installed
    print("\n\nINFO: Checking for dependencies:")
    print("N" * 79)

    try:
        print("\n\n--->Installing mamba")
        os.system("conda install mamba -y -n base -c conda-forge")
        print("\n--->mamba installed... OK")
        conda = 'mamba'
    except BaseException as e:
        print(e)
        print("Could not install mamba, using conda...")
        conda = 'conda'

    try:
        print(f"\n\n--->Cleaning up {conda} cache")
        os.system("mamba clean -q -y --all")
        print(f"\n--->{conda} cache... OK")
    except BaseException as e:
        print(e)
        print(f"Could not clean {conda} cache, aborting install...")
        return 1

    try:
        print("\n\n--->Updating base environment python")
        os.system(f"{conda} update -q -y -n base -c defaults python")
        print("\n--->python update... OK")
    except BaseException as e:
        print(e)
        print("Could not update python, aborting install...")
        return 1

    try:
        print(f"\n\n--->Updating base {conda}")
        os.system(f"{conda} update -q -y -n base -c defaults conda")
        print("\n--->{conda} update... OK")
    except BaseException as e:
        print(e)
        print("Could not update conda, aborting install...")
        raise FileNotFoundError

    try:
        print("\n\n--->Upgrading pip...")
        os.system(f"{conda} install -q -y -n base -c defaults pip --force-reinstall")
        print("\n--->pip upgrade... OK")
    except BaseException as e:
        print(e)
        print("Could not upgrade pip, aborting install...")
        raise FileNotFoundError

    try:
        print("\n\n--->Installing git")
        os.system(f"{conda} install -q -y git")
        print("\n\n--->git... OK")
    except BaseException as e:
        print(e)
        print("Not found: git, aborting install...")
        raise FileNotFoundError

    try:
        print("\n\n--->Updating remaning base packages...")
        os.system(f"{conda} update -q -y -n base -c defaults --all")
        print("\n--->Update of remaining packages... OK")
    except BaseException as e:
        print(e)
        print("Could not update remaining packages, trying to continue install...")

    print("N" * 79)
    print("All dependencies OK.")
    return 0


def create_environment(env_name="iblenv", use_conda_yaml=False, resp=False):
    if use_conda_yaml:
        os.system("mamba env create -f environment.yaml")
        return
    print(f"\n\nINFO: Installing {env_name}:")
    print("N" * 79)
    # Checks if env is already installed
    env = get_env_folder(env_name=env_name)
    print(env)
    # Creates commands
    create_command = f"mamba create -y -n {env_name} python=3.7.11"
    remove_command = f"mamba env remove -y -n {env_name}"
    # Installes the env
    if env:
        print(
            "Found pre-existing environment in {}".format(env),
            "\nDo you want to reinstall the environment? (y/n):",
        )
        user_input = input() if not resp else resp
        print(user_input)
        if user_input == "y":
            os.system(remove_command)
            shutil.rmtree(env, ignore_errors=True)
            return create_environment(env_name=env_name)
        elif user_input != "n" and user_input != "y":
            print("Please answer 'y' or 'n'")
            return create_environment(env_name=env_name)
        elif user_input == "n":
            return
    else:
        os.system(create_command)

    print("N" * 79)
    print(f"{env_name} installed.")


def install_iblrig(env_name: str = "iblenv") -> None:
    print(f"\n\nINFO: Checking iblrig dependencies in {env_name}:")
    print("N" * 79)
    pip = get_env_python(env_name=env_name, rpip=True)
    os.system(f"{pip} install --no-warn-script-location -e .")
    print("N" * 79)
    print(f"iblrig dependencies installed in {env_name}.")


def configure_iblrig_params(env_name: str = "iblenv", resp=False):
    print("\n\nINFO: Setting up default project config in ../iblrig_params:")
    print("N" * 79)
    iblenv = get_env_folder(env_name=env_name)
    if iblenv is None:
        msg = f"Can't configure iblrig_params, {env_name} not found"
        raise ValueError(msg)
    python = get_env_python(env_name=env_name)
    iblrig_params_path = IBLRIG_ROOT_PATH.parent / "iblrig_params"
    if iblrig_params_path.exists():
        print(
            f"Found previous configuration in {str(iblrig_params_path)}",
            "\nDo you want to reset to default config? (y/n)",
        )
        user_input = input() if not resp else resp
        print(user_input)
        if user_input == "n":
            return
        elif user_input == "y":
            subprocess.call([python, "setup_default_config.py", str(iblrig_params_path)])
        elif user_input != "n" and user_input != "y":
            print("\n Please select either y of n")
            return configure_iblrig_params(env_name=env_name)
    else:
        iblrig_params_path.mkdir(parents=True, exist_ok=True)
        subprocess.call([python, "setup_default_config.py", str(iblrig_params_path)])


def install_bonsai(resp=False):
    print("\n\nDo you want to install Bonsai now? (y/n):")
    user_input = input() if not resp else resp
    print(user_input)
    if user_input == "y":
        if sys.platform not in ["Windows", "windows", "win32"]:
            print('Skipping Bonsai installation on non-Windows platforms')
            return
        here = os.getcwd()
        os.chdir(os.path.join(IBLRIG_ROOT_PATH, "Bonsai"))
        subprocess.call("setup.bat")
        os.chdir(here)
    elif user_input != "n" and user_input != "y":
        print("Please answer 'y' or 'n'")
        return install_bonsai()
    elif user_input == "n":
        return


def main(args):
    try:
        check_dependencies()
        create_environment(
            env_name=args.env_name,
            use_conda_yaml=args.use_conda,
            resp=args.reinstall_response,
        )
        install_iblrig(env_name=args.env_name)
        configure_iblrig_params(env_name=args.env_name, resp=args.config_response)
        install_bonsai(resp=args.bonsai_response)
    except BaseException as msg:
        print(msg, "\n\nSOMETHING IS WRONG: Bad! Bad install file!")
    return


if __name__ == "__main__":
    RESPONSES = ["y", "n", False]
    parser = argparse.ArgumentParser(description="Install iblrig")
    parser.add_argument(
        "--env-name",
        "-n",
        required=False,
        default="iblenv",
        help="Environment name for IBL rig installation",
    )
    parser.add_argument(
        "--use-conda",
        required=False,
        default=False,
        action="store_true",
        help="Use conda YAML file to creat environment and install deps.",
    )
    parser.add_argument(
        "--config-response",
        required=False,
        default=False,
        help="Use this response when if asked for resetting default config",
    )
    parser.add_argument(
        "--bonsai-response",
        required=False,
        default=False,
        help="Use this response when asked if you want to install Bonsai",
    )
    parser.add_argument(
        "--reinstall-response",
        required=False,
        default=False,
        help="Use this response when if asked to reinstall env",
    )

    args = parser.parse_args()
    print(type(args.use_conda))
    RUN = 1
    if args.use_conda:
        args.env_name = "iblenv"
    if args.bonsai_response not in RESPONSES:
        print(
            f"Invalid --bonsai-response argument {args.bonsai_response}",
            "\nPlease use {RESPONSES})",
        )
        RUN = 0
    if args.config_response not in RESPONSES:
        print(
            f"Invalid --config-response argument {args.config_response}",
            "\nPlease use {RESPONSES})",
        )
        RUN = 0
    if args.reinstall_response not in RESPONSES:
        print(
            f"Invalid --reinstall-response argument {args.reinstall_response}",
            "\nPlease use {RESPONSES})",
        )
        RUN = 0

    if RUN:
        main(args)

    print("\n\nINFO: iblrig installation EoF")
