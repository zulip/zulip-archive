#!/bin/bash
set -e

zulip_organization_url=$1
zulip_bot_email=$2
zulip_bot_api_key=$3
github_personal_access_token=$4
delete_history=$5
archive_branch=$6

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
pip3 install zulip==0.6.3
pip3 install pyyaml==5.2

# GitHub pages API is in Preview mode. This might break in future.
auth_header="Authorization: Bearer ${github_personal_access_token}"
accept_header="Accept: application/vnd.github.switcheroo-preview+json"
page_api_url="https://api.github.com/repos/${GITHUB_REPOSITORY}/pages"
# Enable GitHub pages
curl -H "$auth_header" -H "$accept_header" --data "{\"source\":{\"branch\":\"${archive_branch}\"}}" "$page_api_url"

print_site_url_code="import sys, json; print(json.load(sys.stdin)['html_url'])"
github_pages_url_with_trailing_slash=$(curl -H "${auth_header}" $page_api_url | python3 -c "${print_site_url_code}")
github_pages_url=${github_pages_url_with_trailing_slash%/}

cp default_settings.py settings.py
cp $streams_config_file_path .

crudini --set zuliprc api site $zulip_organization_url
crudini --set zuliprc api key $zulip_bot_api_key
crudini --set zuliprc api email $zulip_bot_email

export PROD_ARCHIVE=true
export SITE_URL=$github_pages_url
export HTML_DIRECTORY=$html_dir_path
export JSON_DIRECTORY=$json_dir_path
export HTML_ROOT=""
export ZULIP_ICON_URL="${github_pages_url}/assets/img/zulip.svg"

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

if [[ "$delete_history" == "true" ]]
then
    echo "resetting"
    rm -rf .git
    git config --global init.defaultBranch "$archive_branch"
    git init
fi

git config --global user.email "zulip-archive-bot@users.noreply.github.com"
git config --global user.name "Archive Bot"

git add -A
git commit -m "Update archive."

git remote add origin2 https://${GITHUB_ACTOR}:${github_personal_access_token}@github.com/${GITHUB_REPOSITORY}

git push origin2 HEAD:$archive_branch -f

echo "pushed"

echo "Zulip Archive published/updated in ${github_pages_url}"
