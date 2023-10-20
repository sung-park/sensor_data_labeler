#!/bin/bash

# 먼저 adb devices 명령어를 사용하여 연결된 디바이스 목록을 가져옵니다.
devices=$(adb devices | grep -E '^[0-9A-Za-z]+' | awk '{print $1}')

# 만약 연결된 디바이스가 2개 미만이면 오류 메시지 출력
if [ $(echo "$devices" | wc -l) -lt 2 ]; then
  echo "2개 이상의 디바이스가 연결되어 있어야 합니다."
  exit 1
fi

# 디바이스 목록을 배열로 변환
echo "$devices"
devices=($devices)

# GNU 병렬을 사용하여 각 디바이스에 대해 adb shell date 명령어 실행
parallel -j9 --tagstring '{}:' "adb -s {} shell date +%s.%3N" ::: "${devices[@]}"
