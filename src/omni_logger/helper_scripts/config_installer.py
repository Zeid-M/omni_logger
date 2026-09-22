"""
Configuration installer class to install the config files that is essential to the project to run
"""

import argparse
import os
import pathlib
import shutil

import toml


class ConfigurationInstaller:
    """
    A static class to install the configuration files to the config directory.
    """

    @classmethod
    def install_configuration(cls, force_reinstall: bool = False):
        """Main entrypoint to install the configuration"""

        config_path_environ = "OMNILOGGER_ROOT_PATH_FOR_DYNACONF"
        cls.check_if_environment_variable_exist(config_path_environ)

        # prepare environment paths
        source_dir = pathlib.Path(
            pathlib.Path(__file__).parents[1],
            "config",
            "config_templates",
        )

        target_dir = pathlib.Path(os.environ.get(config_path_environ))  # type: ignore

        # Create target directory if not exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Do for each config file
        is_there_modified_config = False
        for source_file_path in source_dir.iterdir():

            # source_file_path = source_file_path
            target_file_path = target_dir.joinpath(
                source_file_path.name.replace(".example", "")
            )

            # Copy config file if not exist and exit
            if not target_file_path.exists() or force_reinstall:
                print(
                    f"Copying new configuration file {source_file_path.name.replace('.example', '')}"
                )
                shutil.copy(source_file_path, target_file_path)
                continue

            # If file exist
            # Compare configuration structure
            # Skip non toml file because we can't compare schema
            if source_file_path.name.endswith(".toml") and not cls.is_toml_schema_match(
                source_file_path, target_file_path
            ):
                print(
                    f"Configuration file {source_file_path.name} structure changed, "
                    "copying new one with .new extension"
                )
                shutil.copy(source_file_path, target_file_path + ".new")  # type: ignore
                is_there_modified_config = True
        if is_there_modified_config:
            raise RuntimeError(
                "You need to update your configuration files, "
                f"new config schema added as .new files in {target_dir}"
            )

        print("Configuration files installed successfully")

    @classmethod
    def check_if_environment_variable_exist(cls, var_name: str):
        """To check the environment variable exist and print the value"""
        print("Checking environment variable:", var_name)
        if not os.environ.get(var_name):
            raise RuntimeError(f"You need to set {var_name} as an environment variable")
        print(f"{var_name} is set with value: {os.environ.get(var_name)}")

    @classmethod
    def is_toml_schema_match(cls, source_file, target_file):
        """Validate toml structure 'keys' between two files"""
        with (
            open(source_file, "r", encoding="utf-8") as src,
            open(target_file, "r", encoding="utf-8") as tgt,
        ):
            print(f"Checking {os.path.basename(target_file)} file schema")

            def get_all_keys(d):
                keys = []
                for key, value in d.items():
                    keys.append(key)
                    if isinstance(value, dict):
                        keys.extend(get_all_keys(value))
                return keys

            source_content = src.read()
            target_content = tgt.read()

            # file is exact match
            if source_content == target_content:
                return True

            # Compare structure (Keys)
            source_toml = toml.load(source_file)
            target_toml = toml.load(target_file)

            if get_all_keys(source_toml) == get_all_keys(target_toml):
                return True
            else:
                return False


def main():

    print("Configuration installer started")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="delete all config files and start from scratch",
    )
    args = parser.parse_args()
    ConfigurationInstaller.install_configuration(force_reinstall=args.force)


if __name__ == "__main__":
    main()
