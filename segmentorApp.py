import sys
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import glob
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.utils.visualizer import ColorMode,Visualizer
from detectron2.engine import DefaultPredictor
import cv2
import shutil
def inference(im,predictor):
    outputs = predictor(
        im)
    v = Visualizer(im[:, :, ::-1],
                   scale=1,
                   instance_mode=ColorMode.SEGMENTATION
                   )
    for fields in zip(*(outputs["instances"].pred_masks.to('cpu'), outputs["instances"].pred_boxes.to('cpu'),
                        outputs["instances"].scores.to('cpu'))):
        seg = fields[0]
        v.draw_binary_mask(seg.numpy(),alpha=0.1)
    segmented_image = v.get_output().get_image()
    return segmented_image,outputs
def set_model(cfg,model_path,model_name):
    cfg.OUTPUT_DIR=model_path
    cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, model_name)  # path to the model we just trained
def load_config(network_name='mask_rcnn_R_101_C4_3x.yaml',location='./model',model_name='model_final.pth',max_objects=5000,device='cpu',
                nb_classes=1,detection_threshold=0.05,input_size=1000,model_resize=2,overlap_threshold=0.5):
    cfg = get_cfg()

    cfg.merge_from_file(model_zoo.get_config_file(os.path.join('COCO-InstanceSegmentation',network_name)))
    set_model(cfg, location,
              model_name)
    cfg.MODEL.DEVICE = device
    cfg.TEST.DETECTIONS_PER_IMAGE = max_objects
    cfg.MODEL.RPN.POST_NMS_TOPK_TEST = max_objects
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = detection_threshold
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = nb_classes
    # Overlap threshold used for non-maximum suppression (suppress boxes with
    # IoU >= this threshold)
    cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = overlap_threshold
    cfg.INPUT.MIN_SIZE_TEST = input_size*model_resize
    cfg.INPUT.MAX_SIZE_TEST = input_size*model_resize
    return cfg


class Worker(QThread):
    PBValueSig = pyqtSignal(int)
    def __init__(self,parent = None):
        super(Worker,self).__init__(parent)
        self.cfg=load_config(model_name='best.pth')
        self.predictor = None
        self.working = False

    def __del__(self):
        self.working = False
       # self.wait()

    def run(self):
        self.working=True
        self.predictor = DefaultPredictor(self.cfg)
        self.PBValueSig.emit(-1)
        if( not os.path.isdir(self.save_in + '/images')):
            os.mkdir(self.save_in + '/images')
        else:
            shutil.rmtree(self.save_in + '/images')
            os.mkdir(self.save_in + '/images')
        if(os.path.exists(self.save_in + '/results.csv')):
            os.remove(self.save_in + '/results.csv')
        with open(self.save_in + '/results.csv', 'a') as fd:
            row='File,Number of cells'+'\n'
            fd.write(row)

        completed = 0
        nb_files = len(self.files)
        for i in self.files:
            im = cv2.imread(i)
            segmented_image, outputs = inference(im, self.predictor)
            cv2.imwrite(self.save_in + '/images/' + str(os.path.basename(i)), segmented_image[:, :, ::-1])
            nb=len(outputs['instances'].scores)
            with open(self.save_in + '/results.csv', 'a') as fd:
                row = str(os.path.basename(i))+','+str(nb)+'\n'
                fd.write(row)
            completed += 1
            self.PBValueSig.emit(int(completed * (100 / nb_files)))
        self.PBValueSig.emit(-2)
        self.working = False
class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Cell Analyst")
        self.resize(1000, 1000)
        self.centralWidget = QWidget()
        self.centralWidget.setStyleSheet("background-image: url(./backgr.png); background-attachment: fixed")
        self.setCentralWidget(self.centralWidget)
        self.thread = Worker()
        self._createMainwindow()
        self._createActions()
        self._createMenuBar()
        self._connectActions()





    def _createMainwindow(self):
        self.progress = QProgressBar(self)
        self.progress.setGeometry(500, 500 - (120 - 80), 250, 20)
        self.progress.hide()
        self.startBtn = QPushButton('Start', self)
        self.startBtn .move(500, 500)
        self.startBtn.hide()

        #self._createToolBars()
    def _createMenuBar(self):
        menuBar = self.menuBar()
        # Creating menus using a QMenu object
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        selectMenu=fileMenu.addMenu('Select images')
        selectMenu.addAction(self.select_folder_Action)
        selectMenu.addSeparator()
        fileMenu.addSeparator()
        selectMenu.addAction(self.select_file_Action)
        settingMenu = menuBar.addMenu('Setting')
        fileMenu.addSeparator()
        settingMenu.addAction(self.changeprobability)
        fileMenu.addSeparator()
        settingMenu.addAction(self.changeoverlapping)
        fileMenu.addAction(self.exitAction)


        # Creating menus using a title
        helpMenu = menuBar.addMenu("&Help")

    def _createToolBars(self):
        # Using a title
        fileToolBar = self.addToolBar("File")

        # Using a QToolBar object
        editToolBar = QToolBar("Edit", self)
        self.addToolBar(editToolBar)
        # Using a QToolBar object and a toolbar area
        helpToolBar = QToolBar("Help", self)
        self.addToolBar(Qt.LeftToolBarArea, helpToolBar)
    def openFile(self):
        # Logic for opening an existing file goes here...
        self.centralWidget.setText("<b>File > Open...</b> clicked")

    def selectFile(self):
        # Logic for opening an existing file goes here...
        files,_ = QFileDialog.getOpenFileNames(parent=self, caption='Select images of cells',directory='.')
        if(len(files)>0):
            self.thread.files=files
            self.thread.save_in=self.select_saving_root()
            self.startBtn.show()
            self.startBtn.setEnabled(True)

        else:
            QMessageBox.about(self, "Error", "No files")


    def selectFolder(self):
        # Logic for opening an existing file goes here...
        folder= QFileDialog.getExistingDirectory(parent=self, caption='Select directory of cells images', directory='.')
        files=glob.glob(folder + '/**/Ph/*.tif', recursive=True)+glob.glob(folder + '/**/Ph/*.png', recursive=True)+glob.glob(folder + '/**/Ph/*.JPEG', recursive=True)
        if (len(files) > 0):
            self.thread.files=files
            self.thread.save_in=self.select_saving_root()
            self.startBtn.show()
            self.startBtn.setEnabled(True)

        else:
            QMessageBox.about(self, "Error", "No files")


    def _createActions(self):
        # Creating action using the first constructor
        self.select_file_Action = QAction(self)
        self.select_file_Action.setText('By file')
        self.select_folder_Action = QAction(self)
        self.select_folder_Action.setText('By directory')
        self.changeprobability=QAction("&Selection probability", self)
        self.changeoverlapping = QAction("&Overlaping threshold", self)
        # Creating actions using the second constructor
        self.exitAction = QAction("&Exit", self)
        self.helpContentAction = QAction("&Help Content", self)
    def select_saving_root(self):
        saving_directory=QFileDialog.getExistingDirectory(parent=self, caption='Select directory to output results', directory='.')
        return saving_directory
    def _connectActions(self):
        # Connect File actions
        self.select_file_Action.triggered.connect(self.selectFile)
        self.select_folder_Action.triggered.connect(self.selectFolder)
        self.changeprobability.triggered.connect(self.Setprobab)
        self.changeoverlapping.triggered.connect(self.Setoverthresh)
        self.exitAction.triggered.connect(self.close)
        self.startBtn.clicked.connect(self.segmenting)
        self.thread.PBValueSig.connect(self.updateProgressBar)
    def Setprobab(self):
        d, okPressed=QInputDialog.getDouble(self, 'Segmentation Setting', 'Probability Threshold', 0.05,0, 1,2)
        if(okPressed):
            self.thread.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST=d

    def Setoverthresh(self):
        d, okPressed=QInputDialog.getDouble(self, 'Segmentation Setting', 'Overlapping Threshold', 0.5,0, 1,2)
        if (okPressed):
            self.thread.cfg.MODEL.ROI_HEADS.NMS_THRESH_TEST = d
    def segmenting(self):
        #ask about wheere to save
        self.startBtn.setEnabled(False)
        self.thread.start()
    @pyqtSlot(int)
    def updateProgressBar(self, value):
        if(value>=0):
            self.progress.setValue(value)
        elif(value==-1):
            self.progress.show()
            self.progress.setValue(0)
            self.startBtn.setText('Running wait')
        elif(value==-2):
            self.progress.hide()
            QMessageBox.about(self, "Message", "Done")
            self.startBtn.setText('Start')



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())

