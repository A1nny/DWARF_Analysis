#!/bin/bash

# OpenSSL 编译脚本（精简版）
SOURCE_DIR1="./openssl-1.1.1w"  # 修改为您的源码目录
SOURCE_DIR2="./openssl-3.0.17"
BUILD_DIR="./build"
OBJECTIVE_DIR="./all"
OPTIMIZE[0]="O0"
OPTIMIZE[1]="O1"
OPTIMIZE[2]="O2"
OPTIMIZE[3]="O3"

OBJECTIVE_DIR="./all"
PYTHON_NAME="Extract.py"








echo "Please input OS:  'x86' or 'x64' ?"
read OS

echo "Please input Version:  '1.1.1w' or '3.0.17' ?"
read Version

echo "Please input Compiler: 'gcc' or 'clang' or 'MinGW-w64' ?\nType 'A'<->'gcc', 'B'<->'clang', 'C'<->'MinGW-w64' to replace compiler name"
read Compiler

echo "Please enter the level of Optimization: use number 0~3 instead of O0~O3"
read Optimization

if [ "${Version}" = "1.1.1w" ]; then
    SOURCE_DIR=$SOURCE_DIR1
elif [ "${Version}" = "3.0.17" ]; then
    SOURCE_DIR=$SOURCE_DIR2
else
    echo "Input Error"
    exit 1
fi

rm -rf "${SOURCE_DIR}"
tar -xzf "${SOURCE_DIR}".tar.gz
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

COMPILE_CFG_x64_gcc_clang="
.${SOURCE_DIR}/config \
    --prefix=$(pwd)/install \
    no-shared \
    no-asm \
    -g3 \
    -gdwarf-5 \
    -${OPTIMIZE[$Optimization]} \
"

COMPILE_CFG_x64_mingw64="
.${SOURCE_DIR}/Configure \
    mingw64 \
    --cross-compile-prefix=x86_64-w64-mingw32- \
    --prefix=$(pwd)/install \
    no-shared \
    no-asm \
    -g3 \
    -gdwarf-5 \
    -${OPTIMIZE[$Optimization]} \
    -fno-omit-frame-pointer
"

COMPILE_CFG_x86_gcc_clang="
.${SOURCE_DIR}/Configure linux-generic32 \
    --prefix=$(pwd)/build-gcc-i386 \
    no-shared \
    no-asm \
    -g3 \
    -gdwarf-5 \
    -${OPTIMIZE[$Optimization]} \
    -fno-omit-frame-pointer \
    -m32
"

COMPILE_CFG_x86_mingw64="
.${SOURCE_DIR}/Configure \
    mingw \
    --cross-compile-prefix=i686-w64-mingw32- \
    --prefix=$(pwd)/install \
    no-shared \
    no-asm \
    -g3 \
    -gdwarf-5 \
    -${OPTIMIZE[$Optimization]} \
    -fno-omit-frame-pointer
"


if [ "$OS" = "x64" ]; then
	if [[ "$Compiler" = "gcc" || "$Compiler" = "A" || "$Compiler" = "a" ]]; then
		$COMPILE_CFG_x64_gcc_clang
    elif [[ "$Compiler" = "clang" || "$Compiler" = "B" || "$Compiler" = "b" ]]; then
        export CC=clang-14
        export CXX=clang++-14
        $COMPILE_CFG_x64_gcc_clang
    elif [[ "$Compiler" = "MinGW-w64" || "$Compiler" = "C" || "$Compiler" = "c" ]]; then
        $COMPILE_CFG_x64_mingw64
    else
        echo "Input error"
        exit 1
    fi
elif [ "$OS" = "x86" ]; then
    if [[ "$Compiler" = "gcc" || "$Compiler" = "A" || "$Compiler" = "a" ]]; then
		$COMPILE_CFG_x86_gcc_clang
    elif [[ "$Compiler" = "clang" || "$Compiler" = "B" || "$Compiler" = "b" ]]; then
        CC="clang-14 -m32"
        $COMPILE_CFG_x86_gcc_clang
    elif [[ "$Compiler" = "MinGW-w64" || "$Compiler" = "C" || "$Compiler" = "c" ]]; then
        $COMPILE_CFG_x86_mingw64
    else
        echo "Input error"
        exit 1
    fi
else
    echo "Input error"
    exit 1
fi



# 编译
make -j$(nproc)


rm -rf "${OBJECTIVE_DIR}"
mkdir -p "${OBJECTIVE_DIR}"
cd "${OBJECTIVE_DIR}"

ar x ../libcrypto.a
ar x ../libssl.a

cd ..
cd ..

SAVE_PATH="./${Compiler}${Version}${Optimization}.json"

python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${Compiler}" "${Version}" "${Optimization}"

