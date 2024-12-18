import os
import shutil

def build_project():
    """Build the project (placeholder for actual build process)."""
    print("Building project...")
    # Replace with actual build commands
    print("Build complete.")

def deploy_project():
    """Deploy the project."""
    print("Deploying project...")
    # Replace with deployment commands
    print("Deployment complete.")

def clean_build_directory(build_dir="build"):
    """
    Clean the build directory.
    :param build_dir: Path to the build directory to clean.
    """
    print(f"Cleaning build directory: {build_dir}")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print("Build directory cleaned.")
    else:
        print("Build directory does not exist.")

def package_project(build_dir="build", output_file="project_package.zip"):
    """
    Package the project into a zip file.
    :param build_dir: Directory containing the build files.
    :param output_file: Output zip file path.
    """
    print(f"Packaging project from {build_dir} to {output_file}")
    if os.path.exists(build_dir):
        shutil.make_archive(output_file.replace(".zip", ""), "zip", build_dir)
        print("Project packaged successfully.")
    else:
        print("Build directory does not exist. Cannot package project.")
