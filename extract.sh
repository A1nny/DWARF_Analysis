
BUILD_DIR="./build"
OBJECTIVE_DIR="./all_obj"
PYTHON_NAME="Extract.py"
SAVE_PATH="./auto_save.json"
COMPILER="gcc"
VERSION="3.0.17"


cd "${BUILD_DIR}"


rm -rf "${OBJECTIVE_DIR}"
mkdir -p "${OBJECTIVE_DIR}"
cd "${OBJECTIVE_DIR}"

ar x ../libcrypto.a
ar x ../libssl.a

cd ..
cd ..

python3 "${PYTHON_NAME}" "${BUILD_DIR}/${OBJECTIVE_DIR#./}" "${SAVE_PATH}" "${COMPILER}" "${VERSION}"
