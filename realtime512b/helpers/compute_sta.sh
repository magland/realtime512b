DEFAULT_PROTOCOL="FastNoise"
DEFAULT_ARRAY_ID="504"

EXP=$1
shift
FILE_NAME=$1
RAW_DATA_PATH='/home/vyomr/Desktop/data/raw'
echo "Using raw data path: ${RAW_DATA_PATH}"

MEA_PATH="/home/vyomr/Desktop/gitrepos/MEA"
VISION_PATH=${MEA_PATH}/src/Vision7_for_2015DAQ/Vision.jar
NAS_PATH="/run/user/1001/gvfs/smb-share:server=128.95.10.105,share=data/data"
# cp ${NAS_PATH}/h5/${EXP}.h5 /home/vyomr/Desktop/data/h5/

# Get the EI file.
# echo "Computing the EI file for ${EXP}, ${FILE_NAME}."
# java -Xmx8G -cp $VISION_PATH edu.ucsc.neurobiology.vision.calculations.CalculationManager "Electrophysiological Imaging Fast" ${SORT_PATH}${FILE_NAME}/ ${RAW_DATA_PATH}/${EXP}/${FILE_NAME}/ 0.01 20 40 1000000 8

# Run parser
PD_SCRIPT="${MEA_PATH}/database/parse_data.py"
H5_PATH="/home/vyomr/Desktop/data/metadata/h5/${EXP}.h5"
JSON_PATH="/home/vyomr/Desktop/data/metadata/json/${EXP}.json"
# python ${PD_SCRIPT} ${H5_PATH} ${JSON_PATH} -r ${RAW_DATA_PATH}

STA_SCRIPT="${MEA_PATH}/src/analysis/protocol/typing/sta_analysis.py"
python ${STA_SCRIPT} ${EXP} -f ${FILE_NAME} -a rt512 -c ${FILE_NAME} --skip_compute_contour -d 20 -s 1 -x 0.6