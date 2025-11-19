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


#!/bin/bash

# 定义所有可能的参数值
os_list=("x64")
version_list=("1.1.1w" "3.0.17")
compiler_list=("gcc" "clang" "MinGW-w64")
optimization_list=("0" "1" "2" "3")
gcc_list=("gcc12" "gcc14")
clang_list=("clang16" "clang18")

# 编译器名称映射（如果需要显示转换）
declare -A compiler_map=(
    ["A"]="gcc"
    ["B"]="clang" 
    ["C"]="MinGW-w64"
)

# 遍历所有组合
for os in "${os_list[@]}"; do
    for version in "${version_list[@]}"; do
        if [ "${version}" = "1.1.1w" ]; then
            SOURCE_DIR=$SOURCE_DIR1
        elif [ "${version}" = "3.0.17" ]; then
            SOURCE_DIR=$SOURCE_DIR2
        else
            echo "Input Error"
            exit 1
        fi
        COMPILE_CFG_x64_gcc_clang="
        .${SOURCE_DIR}/config \
            --prefix=$(pwd)/install \
            no-shared \
            no-asm \
            -g3 \
            -gdwarf-5 \
            -${OPTIMIZE[$optimization]} \
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
            -${OPTIMIZE[$optimization]} \
            -fno-omit-frame-pointer
        "

        COMPILE_CFG_x86_gcc_clang="
        .${SOURCE_DIR}/Configure linux-generic32 \
            --prefix=$(pwd)/build-gcc-i386 \
            no-shared \
            no-asm \
            -g3 \
            -gdwarf-5 \
            -${OPTIMIZE[$optimization]} \
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

        COMPILE_CFG_x64_gcc10="
        .${SOURCE_DIR}/config \
            --prefix=$(pwd)/install \
            no-shared \
            no-asm \
            -g3 \
            -gdwarf-4 \
            -${OPTIMIZE[$Optimization]} \
        "

        for compiler in "${compiler_list[@]}"; do
            for optimization in "${optimization_list[@]}"; do
                if [[ "$compiler" = "gcc" ]];then
                    for voc in "${gcc_list[@]}"; do
                        echo "Setting compiler version: $voc"
                        
                        ###################################
                        
                        echo ${SOURCE_DIR}
                        rm -rf "${SOURCE_DIR}"
                        tar -xzf "${SOURCE_DIR}".tar.gz
                        
                        rm -rf "${BUILD_DIR}"
                        mkdir -p "${BUILD_DIR}"
                        cd "${BUILD_DIR}"
                        echo $(pwd)
                        #####################################
                        if [[ "$voc" = "gcc10" ]]; then
                            eval $GCC10
                        elif [[ "$voc" = "gcc12" ]]; then
                            eval $GCC12
                        elif [[ "$voc" = "gcc14" ]]; then
                            eval $GCC14
                        elif [[ "$voc" = "gcc13" ]]; then
                            eval $GCC13
                        else
                            echo "Input error"
                            exit 1
                        fi
                        #####################################
                        if [ "$os" = "x64" ]; then
                            compiler="gcc"
                            $COMPILE_CFG_x64_gcc_clang
                        elif [ "$os" = "x86" ]; then
                            compiler="gcc"
                            $COMPILE_CFG_x86_gcc_clang
                        else
                            echo "Input error"
                            exit 1
                        fi
                        #####################################
                        make -j$(nproc)
                        opt=${OPTIMIZE[$optimization]}

                        rm -rf "${OBJECTIVE_DIR}"
                        mkdir -p "${OBJECTIVE_DIR}"
                        cd "${OBJECTIVE_DIR}"

                        ar x ../libcrypto.a
                        ar x ../libssl.a

                        cd ..
                        cd ..
                        opt=${OPTIMIZE[$Optimization]}

                        eval "source /home/user/Desktop/myenv/bin/activate"
                        SAVE_PATH="./${os}${compiler}${voc}_openssl${Version}${OPTIMIZE[$Optimization]}.json"

                        python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${compiler}" "${version}" "${opt}" "${os}" "${voc}"


                    done
                elif [[ "$compiler" = "clang" ]]; then
                    for voc in "${clang_list[@]}"; do
                        echo "Setting compiler version: $voc"
                        if [[ "$voc" = "clang14" ]]; then
                            eval $CLANG14
                        elif [[ "$voc" = "clang16" ]]; then
                            eval $CLANG16
                        elif [[ "$voc" = "clang18" ]]; then
                            eval $CLANG18
                        else
                            echo "Input error"
                            exit 1
                        fi

                        ###################################
                        if [ "${version}" = "1.1.1w" ]; then
                            SOURCE_DIR=$SOURCE_DIR1
                        elif [ "${version}" = "3.0.17" ]; then
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
                        #####################################
                        if [ "$os" = "x64" ]; then
                            compiler="clang"
                            $COMPILE_CFG_x64_gcc_clang
                        elif [ "$os" = "x86" ]; then
                            compiler="clang"
                            $COMPILE_CFG_x86_gcc_clang
                        else
                            echo "Input error"
                            exit 1
                        fi
                        #####################################
                        make -j$(nproc)
                        opt=${OPTIMIZE[$optimization]}

                        rm -rf "${OBJECTIVE_DIR}"
                        mkdir -p "${OBJECTIVE_DIR}"
                        cd "${OBJECTIVE_DIR}"

                        ar x ../libcrypto.a
                        ar x ../libssl.a

                        cd ..
                        cd ..
                        opt=${OPTIMIZE[$Optimization]}

                        eval "source /home/user/Desktop/myenv/bin/activate"
                        SAVE_PATH="./${os}${compiler}${voc}_openssl${Version}${OPTIMIZE[$Optimization]}.json"

                        python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${compiler}" "${version}" "${opt}" "${os}" "${voc}"



                    done
                elif [[ "$compiler" = "MinGW-w64" ]]; then
                    voc=""
                    if [ "${version}" = "1.1.1w" ]; then
                        SOURCE_DIR=$SOURCE_DIR1
                    elif [ "${version}" = "3.0.17" ]; then
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
                    #####################################
                    if [ "$os" = "x64" ]; then
                        compiler="MinGW-w64"
                        $COMPILE_CFG_x64_mingw64
                    elif [ "$os" = "x86" ]; then
                        compiler="MinGW-w64"
                        $COMPILE_CFG_x86_mingw64
                    else
                        echo "Input error"
                        exit 1
                    fi
                    #####################################
                    make -j$(nproc)
                    opt=${OPTIMIZE[$optimization]}

                    rm -rf "${OBJECTIVE_DIR}"
                    mkdir -p "${OBJECTIVE_DIR}"
                    cd "${OBJECTIVE_DIR}"

                    ar x ../libcrypto.a
                    ar x ../libssl.a

                    cd ..
                    cd ..
                    opt=${OPTIMIZE[$Optimization]}

                    eval "source /home/user/Desktop/myenv/bin/activate"
                    SAVE_PATH="./${os}${compiler}${voc}_openssl${Version}${OPTIMIZE[$Optimization]}.json"

                    python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${compiler}" "${version}" "${opt}" "${os}" "${voc}"


                else
                    echo "Input error"
                    exit 1
                fi
                
                # 在这里执行你的编译命令
                # 例如：
                # ./build.sh --os $os --version $version --compiler $compiler --optimization O$optimization
                
                # 如果是用A/B/C代替编译器名称，可以这样转换：
                # compiler_key=""
                # for key in "${!compiler_map[@]}"; do
                #     if [ "${compiler_map[$key]}" = "$compiler" ]; then
                #         compiler_key=$key
                #         break
                #     fi
                # done
                
                

                # if [ "${version}" = "1.1.1w" ]; then
                #     SOURCE_DIR=$SOURCE_DIR1
                # elif [ "${version}" = "3.0.17" ]; then
                #     SOURCE_DIR=$SOURCE_DIR2
                # else
                #     echo "Input Error"
                #     exit 1
                # fi

                # rm -rf "${SOURCE_DIR}"
                # tar -xzf "${SOURCE_DIR}".tar.gz
                # rm -rf "${BUILD_DIR}"
                # mkdir -p "${BUILD_DIR}"
                # cd "${BUILD_DIR}"


                # if [ "$os" = "x64" ]; then
                #     if [[ "$compiler" = "gcc" || "$compiler" = "A" || "$compiler" = "a" ]]; then
                #         compiler="gcc"
                #         $COMPILE_CFG_x64_gcc_clang
                #     elif [[ "$compiler" = "clang" || "$compiler" = "B" || "$compiler" = "b" ]]; then
                #         compiler="clang"
                #         # export CC=clang-14
                #         # export CXX=clang++-14
                #         $COMPILE_CFG_x64_gcc_clang
                #     elif [[ "$compiler" = "MinGW-w64" || "$compiler" = "C" || "$compiler" = "c" ]]; then
                #         compiler="MinGW-w64"
                #         $COMPILE_CFG_x64_mingw64
                #     else
                #         echo "Input error"
                #         exit 1
                #     fi
                # elif [ "$os" = "x86" ]; then
                #     if [[ "$compiler" = "gcc" || "$compiler" = "A" || "$compiler" = "a" ]]; then
                #         compiler="gcc"
                #         $COMPILE_CFG_x86_gcc_clang
                #     elif [[ "$compiler" = "clang" || "$compiler" = "B" || "$compiler" = "b" ]]; then
                #         compiler="clang"
                #         # CC="clang-14 -m32"
                #         $COMPILE_CFG_x86_gcc_clang
                #     elif [[ "$compiler" = "MinGW-w64" || "$compiler" = "C" || "$compiler" = "c" ]]; then
                #         compiler="MinGW-w64"
                #         $COMPILE_CFG_x86_mingw64
                #     else
                #         echo "Input error"
                #         exit 1
                #     fi
                # else
                #     echo "Input error"
                #     exit 1
                # fi



                # # 编译
                # make -j$(nproc)
                # opt=${OPTIMIZE[$optimization]}

                # rm -rf "${OBJECTIVE_DIR}"
                # mkdir -p "${OBJECTIVE_DIR}"
                # cd "${OBJECTIVE_DIR}"

                # ar x ../libcrypto.a
                # ar x ../libssl.a

                # cd ..
                # cd ..
                # opt=${OPTIMIZE[$Optimization]}

                # eval "source /home/user/Desktop/myenv/bin/activate"
                # SAVE_PATH="./${os}${compiler}${voc}_openssl${Version}${OPTIMIZE[$Optimization]}.json"

                # python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${compiler}" "${version}" "${opt}" "${os}" "${voc}"


                                
                # # 可选：添加延迟避免系统负载过高
                # sleep 1
            done
        done
    done
done

echo "所有组合执行完成！"


