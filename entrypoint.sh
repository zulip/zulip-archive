#!/bin/bash
set -e

zulip_realm_url=$1
zulip_bot_api_key=$2
zulip_bot_email=$3
github_personal_access_token=$4

checked_out_repo_path="$(pwd)"
html_dir_path=$checked_out_repo_path
json_dir_path="${checked_out_repo_path}/zulip_json"
_layouts_path="${checked_out_repo_path}/_layouts"
img_dir_path="${checked_out_repo_path}/assets/img"

cd "/zulip-archive-action"

curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
python3 get-pip.py

pip install virtualenv
virtualenv -p python3 .
source bin/activate
pip3 install zulip

# GitHub pages API is in Preview mode. This might break in future.
auth_header="Authorization: Bearer ${github_personal_access_token}"
accept_header="Accept: application/vnd.github.switcheroo-preview+json"
page_api_url="https://api.github.com/repos/${GITHUB_REPOSITORY}/pages"
# Enable GitHub pages
curl -H "$auth_header" -H "$accept_header" --data "source=master" "$page_api_url"

print_site_url_code="import sys, json; print(json.load(sys.stdin)['html_url'])"
github_pages_url_with_trailing_slash=$(curl -H "${auth_header}" $page_api_url | python3 -c "${print_site_url_code}")
github_pages_url=${github_pages_url_with_trailing_slash%/}

cp default_settings.py settings.py

crudini --set zuliprc api site $zulip_realm_url
crudini --set zuliprc api key $zulip_bot_api_key
crudini --set zuliprc api email $zulip_bot_email

export PROD_ARCHIVE=true
export SITE_URL=$github_pages_url
export HTML_DIRECTORY=$html_dir_path
export JSON_DIRECTORY=$json_dir_path
export HTML_ROOT=""
export ZULIP_ICON_URL="${github_pages_url}/assets/img/zulip2.png"

if [ ! -d $json_dir_path ]; then
    mkdir -p $json_dir_path

    mkdir -p $_layouts_path
    cp -rf layouts/* $_layouts_path

    mkdir -p $img_dir_path
    cp assets/img/* $img_dir_path

    python3 archive.py -t
else
    python3 archive.py -i
fi


python3 archive.py -b

cd ${checked_out_repo_path}

git checkout master

git config --global user.email "zulip-archive-bot@users.noreply.github.com"
git config --global user.name "Archive Bot"

git add -A
git commit -m "Update archive."

git remote set-url --push origin https://${GITHUB_ACTOR}:${github_personal_access_token}@github.com/${GITHUB_REPOSITORY}

git push origin master --force

echo "Zulip Archive published/updated in ${github_pages_url}"
