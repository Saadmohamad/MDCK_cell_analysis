dpp = 0.8E-3; // Distance per pixel in mm

// Running in batch mode should speed things up considerably
setBatchMode(true);

var dir1 = getDirectory("Choose folder with images ");
var list = getFileList(dir1);

// create folders for the tifs
var dir1parent = File.getParent(dir1);
var dir1name = File.getName(dir1);
var dir2 = dir1parent+File.separator+dir1name+"--Processed Results";
if (File.exists(dir2)==false) {
	File.makeDirectory(dir2); // new directory for tiff
}

// Initialising stores
ImageName = newArray();
InitialCount = newArray();
CellCount = newArray();
TotalArea = newArray();
Density = newArray();

//This for loop opens each image in the input folder and prompts the user to, one by one, 
for (var i=0; i<list.length; i++) {
	showProgress(i+1, list.length);
	var path=dir1+list[i];
	var names = newArray(nImages); 
	var ids = newArray(nImages);
	open( dir1 + list[i] );
	
	title = getTitle();
	run("Gaussian Blur...", "sigma=1");

	// Filtering to remove noise, then applying local threshold (Phansalkar, radius 5px)
	run("Duplicate...", " ");
	run("Auto Local Threshold", "method=Mean radius=15 parameter_1=0 parameter_2=0 white");
	binaryWin = getTitle();

	// Manually removing any very dark pixels (background), since Mean local threshold will 
	// identify "objects" in this region
	selectWindow(title);
	run("Duplicate...", " ");
	rename("ManBinaryWin");
	run("Subtract Background...", "rolling=50");
	setThreshold(0, 6);
	setOption("BlackBackground", false);
	run("Convert to Mask");
	imageCalculator("Subtract", binaryWin, "ManBinaryWin");
	selectWindow("ManBinaryWin");
	close();

	// Getting extended maxima from filtered image
	selectWindow(title);
	run("Extended Min & Max", "operation=[Extended Maxima] dynamic=2 connectivity=8");
	run("Watershed");
	run("Ultimate Points");
	setThreshold(0, 0);
	setOption("BlackBackground", false);
	run("Convert to Mask");
	run("Invert LUT");
	run("Invert");
	markerWin = getTitle();

	// Running marker-controlled watershed segmentation to split cells
	run("Marker-controlled Watershed", "input="+binaryWin+" marker="+markerWin+" mask="+binaryWin+" binary calculate use");
	setThreshold(0, 0);
	setOption("BlackBackground", false);
	run("Convert to Mask");
	run("Invert LUT");
	thresholdWin = getTitle();

	// Removing some unwanted windows
	selectWindow(binaryWin);
	close();
	selectWindow(markerWin);
	close();
	selectWindow(thresholdWin);
		
	run("Analyze Particles...", "size=20-Infinity show=Masks clear add");	
	count = getValue("results.count");
	title2 = getTitle;
	selectWindow(thresholdWin);
	close();

	// Calculating the mean cell area
	area = 0;
	for (var p = 0; p<count; p++){
		x = getResult("Area", p);
		area = area + x;
	}
	meanArea = area/count;

	selectWindow(title);
	resultCounter = count;
	for (var t = 0; t<count; t++){
		roiArea = getResult("Area", t);
		if (roiArea > (2.5*meanArea)){
			resultCounter = resultCounter + floor(roiArea / meanArea);

			// If this object was considered a cluster, outline in red
			run("Overlay Options...", "stroke=red width=0 fill=none set");
		} else {
			// Outline "single" cells in cyan
			run("Overlay Options...", "stroke=cyan width=0 fill=none set");
		}

		// Adding the current selection
		roiManager("select", t);
		run("Add Selection...");
	}

	close("Results");
	close("Log");
	roiManager("Deselect");
	roiManager("Delete");
	
	// Detecting cell regions
	selectWindow(title2);
	run("Maximum...", "radius=25");
	run("Minimum...", "radius=25");
	run("Analyze Particles...", "size=20-Infinity show=Masks summarize");
	run("Create Selection");
	roiManager("Add");
	
	// Getting total cell area from Summary and converting to um^2 units
	IJ.renameResults("Summary","Results");
	totalArea = getResult("Total Area", 0)*dpp*dpp;
	close("Results");
	
	// Drawing cell outlines
	selectWindow(title);
	run("Overlay Options...", "stroke=white width=0 fill=none set");
	for (var t = 0; t<roiManager("count"); t++){
		roiManager("select", t);
		run("Add Selection...");
	}
	roiManager("Deselect");
	roiManager("Delete");
		
	run("Flatten");
	outpath = dir2+File.separator+title+"--Outlines";
	saveAs("tiff", outpath);
	
	ImageName = Array.concat(ImageName, title);
	InitialCount = Array.concat(InitialCount, count);
	CellCount = Array.concat(CellCount, resultCounter);
	TotalArea = Array.concat(TotalArea, totalArea);
	Density = Array.concat(Density, (resultCounter/(totalArea)));
	
	Array.show("Output", ImageName, InitialCount, CellCount, TotalArea, Density);
	run("Close All");
	
}
 
setBatchMode(false);