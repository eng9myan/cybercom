#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_config="$script_dir/../nginx/cy-com.com.conf"
target_config="/etc/nginx/sites-available/cy-com.com"
enabled_config="/etc/nginx/sites-enabled/cy-com.com"
backup="${target_config}.backup.$(date -u +%Y%m%dT%H%M%SZ)"

if sudo test -f "$target_config"; then
  sudo cp --preserve=mode,ownership,timestamps "$target_config" "$backup"
fi

restore_config() {
  status=$?
  if sudo test -f "$backup"; then
    sudo cp "$backup" "$target_config"
    sudo nginx -t && sudo systemctl reload nginx
  fi
  exit "$status"
}
trap restore_config ERR

sudo install -m 0644 "$source_config" "$target_config"
sudo ln -sfn "$target_config" "$enabled_config"
sudo nginx -t
sudo systemctl reload nginx
trap - ERR

echo "Nginx reverse proxy installed; backup: $backup"
