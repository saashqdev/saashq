#!/bin/bash
set -e
cd ~ || exit

verbosity="${WRENCH_VERBOSITY_FLAG:-}"

start_time=$(date +%s)
echo "::group::Install Wrench"
pip install saashq-wrench
echo "::endgroup::"
end_time=$(date +%s)
echo "Time taken to Install Wrench: $((end_time - start_time)) seconds"

git config --global init.defaultBranch main
git config --global advice.detachedHead false

start_time=$(date +%s)
echo "::group::Init Wrench & Install Saashq"
wrench $verbosity init saashq-wrench --skip-assets --python "$(which python)" --saashq-path "${GITHUB_WORKSPACE}"
echo "::endgroup::"
end_time=$(date +%s)
echo "Time taken to Init Wrench & Install Saashq: $((end_time - start_time)) seconds"

cd ~/saashq-wrench || exit

start_time=$(date +%s)
echo "::group::Install App Requirements"
wrench $verbosity setup requirements --dev
if [ "$TYPE" == "ui" ]
then
  wrench $verbosity setup requirements --node;
fi
end_time=$(date +%s)
echo "::endgroup::"
echo "Time taken to Install App Requirements: $((end_time - start_time)) seconds"