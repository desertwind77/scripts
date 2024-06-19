/*
 * This part is from SmartSharpen.jsx in xtools
 * Download at http://ps-scripts.sourceforge.net/xtools.html
 */
cTID = function(s) { return app.charIDToTypeID(s); };
sTID = function(s) { return app.stringIDToTypeID(s); };

PSClass = function() {};
PSEnum = function() {};
PSEvent = function() {};
PSForm = function() {};
PSKey = function() {};
PSType = function() {};
PSUnit = function() {};
PSString = function() {};

PSEvent.GaussianBlur = cTID('GsnB');
PSEvent.MotionBlur = cTID('MtnB');
PSKey.Angle = cTID('Angl');
PSKey.Amount = cTID('Amnt');
PSKey.Blur = cTID('blur');
PSKey.HighlightMode = cTID('hglM');
PSKey.Radius = cTID('Rds ');
PSKey.ShadowMode = cTID('sdwM');
PSKey.Threshold = cTID('Thsh');
PSKey.Width = cTID('Wdth');
PSString.blurType = sTID('blurType');
PSString.lensBlur = sTID('lensBlur');
PSString.moreAccurate = sTID('moreAccurate');
PSString.preset = sTID('preset');
PSString.smartSharpen = sTID('smartSharpen');
PSUnit.Percent = cTID('#Prc');
PSUnit.Pixels = cTID('#Pxl');

SmartSharpenOptions = function() {
    var self = this;

    self.amount = 100;          // 1% - 500%
    self.radius = 1.0;          // 0.1 px - 64.0 px
    self.blurType = SmartSharpenBlurType.GAUSSIAN_BLUR;
    self.threshold = 0;         // ???
    self.angle = 0;             // 0.0 - 360 ??? only when blurType = MOTION_BLUR
    self.moreAccurate = false;
    self.preset = "Default";    // ???

    self.shadowAmount = 0;      // 0% - 100%
    self.shadowTonalWidth = 50; // 0% - 100%
    self.shadowRadius = 1;      // 1 px - 100 px
    self.shadowMode = sTID('adaptCorrectedTones');

    self.hiliteAmount = 0;      // 0% - 100%
    self.hiliteTonalWidth = 50; // 0% - 100%
    self.hiliteRadius = 1;      // 1 px - 100 px
    self.hiliteMode = sTID('adaptCorrectedTones');

    self.interactive = false;
};
SmartSharpenOptions.typename = "SmartSharpenOptions";

SmartSharpenBlurType = {};
SmartSharpenBlurType.GAUSSIAN_BLUR = PSEvent.GaussianBlur;
SmartSharpenBlurType.LENS_BLUR     = PSString.lensBlur;
SmartSharpenBlurType.MOTION_BLUR   = PSEvent.MotionBlur;

smartSharpen = function( opts ) {
    var ssDesc = new ActionDescriptor();

    ssDesc.putUnitDouble( PSKey.Amount, PSUnit.Percent, opts.amount );
    ssDesc.putUnitDouble( PSKey.Radius, PSUnit.Pixels, opts.radius );
    ssDesc.putInteger( PSKey.Threshold, opts.threshold );
    ssDesc.putInteger( PSKey.Angle, opts.angle );
    ssDesc.putBoolean( PSString.moreAccurate, opts.moreAccurate );
    ssDesc.putEnumerated( PSKey.Blur, PSString.blurType, opts.blurType );
    ssDesc.putString( PSString.preset, opts.preset );

    var shDesc = new ActionDescriptor();
    shDesc.putUnitDouble( PSKey.Amount, PSUnit.Percent, opts.shadowAmount );
    shDesc.putUnitDouble( PSKey.Width, PSUnit.Percent, opts.shadowTonalWidth );
    shDesc.putInteger( PSKey.Radius, opts.radius );

    ssDesc.putObject( PSKey.ShadowMode, opts.shadowMode, shDesc );

    var hiDesc = new ActionDescriptor();
    hiDesc.putUnitDouble( PSKey.Amount, PSUnit.Percent, opts.hiliteAmount );
    hiDesc.putUnitDouble( PSKey.Width, PSUnit.Percent, opts.hiliteTonalWidth );
    hiDesc.putInteger( PSKey.Radius, opts.hiliteRadius );

    ssDesc.putObject( PSKey.HighlightMode, opts.hiliteMode, hiDesc );

    executeAction( PSString.smartSharpen, ssDesc,
        ( opts.interactive ? DialogModes.ALL : DialogModes.NO ) );
};

doSmartSharpen = function( amount, radius ) {
    var opts = new SmartSharpenOptions()
	opts.amount = amount
	opts.radius = radius
	smartSharpen( opts )
}

/* --------------------------------------------------------------- */
// Save previous rulerUnits
starterRulerUnits = app.preferences.rulerUnits
// Set the new rulerUnits to PIXELS
app.preferences.rulerUnits = Units.PIXELS
// get a reference to the current (active) document and store
// it in a variable named "doc"
doc = app.activeDocument;
// Flatten the doc cause it may have multiple layers
doc.flatten()
// Change the color mode to LAB
doc.changeMode( ChangeMode.LAB )
// Select the Lightness channel cause we want to resize and sharpen in
// the Lightness channel.
doc.activeChannels = [ doc.channels.getByName( 'Lightness' ) ]

function doStepResize() {
    var outputSize = 1400
    var step = 500
    var tmp
    var nextSize

    if( doc.height > doc.width ) {
        currentSize = doc.height.value
    } else {
        currentSize = doc.width.value
    }

    while( currentSize > outputSize ) {
        x = Math.floor( currentSize / step )
        nextSize = ( x  - 1 ) * step
        if( nextSize <= outputSize ) nextSize = outputSize

        if( doc.height > doc.width ) {
            doc.resizeImage( null, UnitValue( nextSize, 'px' ), null,
						     ResampleMethod.BICUBIC );
        } else {
            doc.resizeImage( UnitValue( nextSize, 'px' ), null, null,
						     ResampleMethod.BICUBIC );
        }

        currentSize = nextSize

        if ( currentSize == 1400 ) {
            doSmartSharpen( 200, 0.2 )
        } else if( ( currentSize == 1500 ) && ( currentSize == 2000 ) ) {
            doSmartSharpen( 150, 0.2 )
        } else if( currentSize == 2500 ) {
            doSmartSharpen( 100, 0.2 )
        } else {
            doSmartSharpen( 60, 0.3 )
        }
    }
}

function doNormalResize( outputSize ) {
    if( doc.height > doc.width ) {
        doc.resizeImage( null, UnitValue( outputSize, 'px' ), null,
						 ResampleMethod.BICUBIC );
    } else {
        doc.resizeImage( UnitValue( outputSize, 'px' ), null, null,
						 ResampleMethod.BICUBIC );
    }

    doSmartSharpen( 100, 0.2 )
}

var outputSize = 1920
doNormalResize( outputSize )

// Change color mode back to RGB
doc.changeMode( ChangeMode.RGB )

var docName = doc.name
var docNameOnly = docName.substr( 0, docName.lastIndexOf( '.' ) ) || docName
var newName = docNameOnly + '.jpg'

// Save the resized doc to the new file
jpgFile = new File( doc.path + '/' + newName )
jpgSaveOptions = new JPEGSaveOptions()
jpgSaveOptions.embedColorProfile = true
jpgSaveOptions.formatOptions = FormatOptions.STANDARDBASELINE
jpgSaveOptions.matte = MatteType.NONE
jpgSaveOptions.quality = 12
app.activeDocument.saveAs( jpgFile, jpgSaveOptions, true,
                           Extension.LOWERCASE )

// Restore the original rulerUnits
app.preferences.rulerUnits = starterRulerUnits
