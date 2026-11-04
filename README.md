# action-practice

![Build](https://github.com/mierule7/action-practice/actions/workflows/build.yml/badge.svg)

A small calculator web app with a GitHub Actions pipeline: quality gate, image build, then manual promotion dev, uat, prod using the same Build ID.

## How to deploy

1. Push to `main`. Build Image runs and publishes an image with a Build ID, for example 12.
2. Actions > Manual Deploy > Run workflow: choose `dev`, type the Build ID, run.
3. Repeat with `uat`, then `prod`, using the same Build ID. Approve when prompted.

## How to roll back

Run Manual Deploy with `prod` and the last known-good Build ID.
Find it in the Deployments page or the tag list under Packages.
