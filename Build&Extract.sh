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
PYTHON_NAME="/home/user/Desktop/sql/extract.py"








echo "Please input OS:  'x86' or 'x64' ?"
read OS

echo "Please input Version:  '1.1.1w' or '3.0.17' ?"
read Version

echo "Please input Compiler: 'gcc' or 'clang' or 'MinGW-w64' ?\nType 'A'<->'gcc', 'B'<->'clang', 'C'<->'MinGW-w64' to replace compiler name"
read Compiler

if [[ "$Compiler" = "gcc" || "$Compiler" = "A" || "$Compiler" = "a" ]]; then
    echo "Please enter the version of Compiler: gcc10, gcc12, gcc13, gcc14"
    read VoC
elif [[ "$Compiler" = "clang" || "$Compiler" = "B" || "$Compiler" = "b" ]]; then
    echo "Please enter the version of Compiler: clang14, clang16, clang18"
    read VoC
   
elif [[ "$Compiler" = "MinGW-w64" || "$Compiler" = "C" || "$Compiler" = "c" ]]; then
    VoC=""
else
    echo "Input Error"
    exit 1
fi


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

GCC10="
export CC=/usr/bin/gcc-10
export CXX=/usr/bin/g++-10
"

GCC12="
export CC=/usr/bin/gcc-12
export CXX=/usr/bin/g++-12
"


GCC14="
export CC=/usr/bin/gcc-14
export CXX=/usr/bin/g++-14
"

CLANG16="
export CC=/usr/bin/clang-16
export CXX=/usr/bin/clang++-16
"

CLANG18="
export CC=/usr/bin/clang-18
export CXX=/usr/bin/clang++-18
"

CLANG14="
export CC=/usr/bin/clang-14
export CXX=/usr/bin/clang++-14
"



COMPILE_CFG_x64_gcc10="
.${SOURCE_DIR}/config \
    --prefix=$(pwd)/install \
    no-shared \
    no-asm \
    -g3 \
    -gdwarf-4 \
    -${OPTIMIZE[$Optimization]} \
"

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

echo ${Voc}
if [ "$OS" = "x64" ]; then
	if [[ "$Compiler" = "gcc" || "$Compiler" = "A" || "$Compiler" = "a" ]]; then
        if [[ "$VoC" = "gcc10" ]]; then
            eval $GCC10
        elif [[ "$VoC" = "gcc12" ]]; then
            eval $GCC12
            echo "gcc12 is set"
        elif [[ "$VoC" = "gcc14" ]]; then
            eval $GCC14
        elif [[ "$VoC" = "gcc13" ]]; then
            echo "gcc13 is not needed currently"
        else
            echo "Input error"
            exit 1
        fi
        compiler="gcc"
		$COMPILE_CFG_x64_gcc_clang
    elif [[ "$Compiler" = "clang" || "$Compiler" = "B" || "$Compiler" = "b" ]]; then
        if [[ "$VoC" = "clang14" ]]; then
            eval $CLANG14
        elif [[ "$VoC" = "clang16" ]]; then
            eval $CLANG16
        elif [[ "$VoC" = "clang18" ]]; then
            eval $CLANG18
        else
            echo "Input error"
            exit 1
        fi
        compiler="clang"
        $COMPILE_CFG_x64_gcc_clang
    elif [[ "$Compiler" = "MinGW-w64" || "$Compiler" = "C" || "$Compiler" = "c" ]]; then
        compiler="MinGW-w64"
        $COMPILE_CFG_x64_mingw64
    else
        echo "Input error"
        exit 1
    fi
elif [ "$OS" = "x86" ]; then
    if [[ "$Compiler" = "gcc" || "$Compiler" = "A" || "$Compiler" = "a" ]]; then
        if [[ "$VoC" = "gcc10" ]]; then
            eval $GCC10
        elif [[ "$VoC" = "gcc12" ]]; then
            eval $GCC12
        elif [[ "$VoC" = "gcc14" ]]; then
            eval $GCC14
        elif [[ "$VoC" = "gcc13" ]]; then
            echo "gcc13 does not need build"
        else
            echo "Input error"
            exit 1
        fi
        compiler="gcc"
		$COMPILE_CFG_x86_gcc_clang
    elif [[ "$Compiler" = "clang" || "$Compiler" = "B" || "$Compiler" = "b" ]]; then
        if [[ "$VoC" = "clang14" ]]; then
            eval $CLANG14
        elif [[ "$VoC" = "clang16" ]]; then
            eval $CLANG16
        elif [[ "$VoC" = "clang18" ]]; then
            eval $CLANG18
        else
            echo "Input error"
            exit 1
        fi
        compiler="clang"
        CC="clang-14 -m32"
        $COMPILE_CFG_x86_gcc_clang
    elif [[ "$Compiler" = "MinGW-w64" || "$Compiler" = "C" || "$Compiler" = "c" ]]; then
        compiler="MinGW-w64"
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
opt=${OPTIMIZE[$Optimization]}

eval "source /home/user/Desktop/myenv/bin/activate"

SAVE_PATH="./${OS}${compiler}${VoC}_openssl${Version}${OPTIMIZE[$Optimization]}.json"

python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${compiler}" "${Version}" "${opt}" "${OS}" "${VoC}"

# python3 "/home/user/Desktop/sql/extract.py" "./build/all"  "./1.json" "gcc" "1.1.1w" "O2" "x64" "gcc12"
