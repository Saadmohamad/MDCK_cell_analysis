# cell_segm_app

This Mac app uses Mask_RCNN from facebook detectron2 library.

Installation:
- Donwload the souece code

- install anaconda that is in your browser go to https://repo.anaconda.com/archive/Anaconda3-2020.11-MacOSX-x86_64.pkg 
		(This will download Anaconda’s Mac “64-bit Graphical installer”)
- Create conda enviorment: conda create -n segm python=3.8.5 
- Activate the enviorment: source activate segm
- Install pytorch and torch vision, we tested this version on torch==1.7 and torchvision==0.8.1
- Install opencv: pip install opencv-python-headless==4.5.1.48
- install detectron2, we tested this version on: CC=clang CXX=clang++ python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
- install QT: pip install PyQt5==5.15.2



Running:
- Open Terminal
- Go to model “cd path/to/segmentation”
- Type “conda activate segm”
- Finally, type “python segmentorApp.py”



