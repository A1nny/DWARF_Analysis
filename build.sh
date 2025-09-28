#!/bin/bash

# OpenSSL 编译脚本（精简版）
SOURCE_DIR="./openssl-3.0.17"  # 修改为您的源码目录
BUILD_DIR="./build"
OBJECTIVE_DIR= "./all_obj"
NUM_JOBS=$(nproc)

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

echo "${SOURCE_DIR}"

# 配置
".${SOURCE_DIR}/config" \
    --prefix=$(pwd)/install \
    no-shared \
    no-asm \
    -g3 \
    -gdwarf-5 \
    -O2 \

# 编译
make -j$(nproc)
