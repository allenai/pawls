rm ~/.docker/config.json
docker-compose up --build

cd $proj_root/cli
pip install -e "."

cd $proj_root
pawls add downloads/rfps
pawls preprocess pymupdf skiff_files/apps/pawls/papers

rm -rf skiff_files/apps/pawls/papers/*
