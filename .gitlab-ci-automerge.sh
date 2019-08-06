#!/bin/sh
set -e
set -x

echo "Processing for merge requests."

HOST="${HOST}api/v4/projects/"

TARGET_BRANCH=$RELEASE

BODY="{
    \"id\": ${CI_PROJECT_ID},
    \"source_branch\": \"${CI_COMMIT_REF_NAME}\",
    \"target_branch\": \"${TARGET_BRANCH}\",
    \"remove_source_branch\": true,
    \"title\": \"WIP RELEASE: ${CI_COMMIT_REF_NAME}\",
    \"assignee_id\":\"${GITLAB_USER_ID}\"
}";

LISTMR=`curl --silent "${HOST}${CI_PROJECT_ID}/merge_requests?state=opened" --header "PRIVATE-TOKEN:${PRIVATE_TOKEN}"`;
MATCHES=`echo ${LISTMR} | jq ".[] | {target_branch: .target_branch | match(\"${TARGET_BRANCH}\"), source_branch: .source_branch | match(\"${CI_COMMIT_REF_NAME}\")}"`;

# No MR found, let's create a new one
if [ -z "${MATCHES}" ]; then
    curl -X POST "${HOST}${CI_PROJECT_ID}/merge_requests" \
        --header "PRIVATE-TOKEN:${PRIVATE_TOKEN}" \
        --header "Content-Type: application/json" \
        --data "${BODY}";

    echo "Opened a new merge request: WIP RELEASE: ${CI_COMMIT_REF_NAME} and assigned to you";
fi

# Test
TARGET_BRANCH="${RELEASE}-test"

BODY="{
    \"id\": ${CI_PROJECT_ID},
    \"source_branch\": \"${CI_COMMIT_REF_NAME}\",
    \"target_branch\": \"${TARGET_BRANCH}\",
    \"remove_source_branch\": false,
    \"title\": \"WIP TEST: ${CI_COMMIT_REF_NAME}\",
    \"assignee_id\":\"${GITLAB_USER_ID}\"
}";

LISTMR=`curl --silent "${HOST}${CI_PROJECT_ID}/merge_requests?state=opened" --header "PRIVATE-TOKEN:${PRIVATE_TOKEN}"`;
MATCHES=`echo ${LISTMR} | jq ".[] | {target_branch: .target_branch | match(\"${TARGET_BRANCH}\"), source_branch: .source_branch | match(\"${CI_COMMIT_REF_NAME}\")}"`;

# No MR found, let's create a new one
if [ -z "${MATCHES}" ]; then
    curl -X POST "${HOST}${CI_PROJECT_ID}/merge_requests" \
        --header "PRIVATE-TOKEN:${PRIVATE_TOKEN}" \
        --header "Content-Type: application/json" \
        --data "${BODY}";

    echo "Opened a new merge request: WIP TEST: ${CI_COMMIT_REF_NAME} and assigned to you";
fi


