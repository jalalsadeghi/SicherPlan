#!/usr/bin/env bash
set -euo pipefail

test -f mobile/.env.example
test -f mobile/lib/config/app_config.dart

grep -q '^SP_ENV=' mobile/.env.example
grep -q '^SP_API_BASE_URL=' mobile/.env.example
grep -q 'class AppConfig' mobile/lib/config/app_config.dart
grep -q 'String.fromEnvironment' mobile/lib/config/app_config.dart
dart format --set-exit-if-changed mobile/lib/config/app_config.dart
