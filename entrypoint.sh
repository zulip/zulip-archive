#!/bin/bash
set -e

zulip_organization_url=$1
zulip_bot_email=$2
zulip_bot_api_key=$3
github_token=$INPUT_GITHUB_TOKEN
delete_history=$5
archive_branch=$6
github_personal_access_token=$7
zuliprc=$INPUT_ZULIPRC
site_url=$INPUT_SITE_URL

github_personal_access_token=${github_personal_access_token:-NOT_SET}

if [ $github_personal_access_token != "NOT_SET" ]; then
    echo "'github_personal_access_token' input has been deprecated."
    echo "To migrate to the new setup, you have to replace it with"
    echo "github_token. For more info, see"
    echo 'https://github.com/zulip/zulip-archive#step-5---enable-zulip-archive-action'
    exit 1
fi

# This is a temporary workaround.
# See https://github.com/actions/checkout/issues/766
git config --global --add safe.directory "$GITHUB_WORKSPACE"

checked_out_repo_path="$(pwd)"
html_dir_path=$checked_out_repo_path
json_dir_path="${checked_out_repo_path}/zulip_json"
img_dir_path="${checked_out_repo_path}/assets/img"
streams_config_file_path="${checked_out_repo_path}/streams.yaml"
initial_sha="$(git rev-parse HEAD)"

if [ ! -f $streams_config_file_path ]; then
    echo "Missing streams.yaml file."
    exit 1
fi

cd "/zulip-archive-action"

curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
python3 get-pip.py

pip install virtualenv
virtualenv -p python3 .
source bin/activate
pip3 install -r requirements.txt
# crudini is not available as an Alpine pkg, so we install via pip.
pip3 install crudini

if [ -z "$site_url" ]; then
    echo "Setting up site URL from GitHub pages API"
    # Uses GitHub pages API
    # https://docs.github.com/en/rest/pages
    auth_header="Authorization: Bearer ${github_token}"
    accept_header="Accept: application/vnd.github+json"
    version_header="X-GitHub-Api-Version: 2022-11-28"
    page_api_url="https://api.github.com/repos/${GITHUB_REPOSITORY}/pages"

    print_site_url_code="import sys, json; print(json.load(sys.stdin)['html_url'])"
    # Get the GitHub pages URL
    github_pages_url_with_trailing_slash=$(curl -L -H "$accept_header" -H "$auth_header" -H "$version_header" "$page_api_url" | python3 -c "${print_site_url_code}")
    site_url=${github_pages_url_with_trailing_slash%/}
else
    site_url=${site_url%/}
fi

cp default_settings.py settings.py
cp $streams_config_file_path .

if [ -z "$zuliprc" ]; then
	echo "Setting up Zulip details via 3 variables (zulip_organization_url, zulip_bot_key, zulip_bot_email)"
	echo "is deprecated. The current simpler method is to just set the zuliprc content in the GH secrets."
	crudini --set zuliprc api site "$zulip_organization_url"
	crudini --set zuliprc api key "$zulip_bot_api_key"
	crudini --set zuliprc api email "$zulip_bot_email"
else
	echo "$zuliprc" > zuliprc
fi

export PROD_ARCHIVE=true
export SITE_URL=$site_url
export HTML_DIRECTORY=$html_dir_path
export JSON_DIRECTORY=$json_dir_path
export HTML_ROOT=""
export ZULIP_ICON_URL="${site_url}/assets/img/zulip.svg"

if [ ! -d $json_dir_path ]; then
    mkdir -p $json_dir_path

    mkdir -p $img_dir_path
    cp assets/img/* $img_dir_path

    python3 archive.py -t
else
    python3 archive.py -i
fi


python3 archive.py -b

cd ${checked_out_repo_path}

git checkout $archive_branch

git fetch origin

current_sha="$(git rev-parse origin/${archive_branch})"

if [[ "$current_sha" != "$initial_sha" ]]
then
  echo "Archive update failed, commits have been added while processing"
  exit 1
fi

echo "delete history: $delete_history"

git config --global user.email "zulip-archive-bot@users.noreply.github.com"
git config --global user.name "Archive Bot"

git add -A
if [[ "$delete_history" == "true" ]]
then
	git commit --amend -m "Update archive."
	# Cleanup loose objects
	git gc
else
	git commit -m "Update archive."
fi

git remote add origin2 https://${GITHUB_ACTOR}:${github_token}@github.com/${GITHUB_REPOSITORY}

git push origin2 HEAD:$archive_branch -f

echo "pushed"

echo "Zulip Archive published/updated in ${github_pages_url}"
