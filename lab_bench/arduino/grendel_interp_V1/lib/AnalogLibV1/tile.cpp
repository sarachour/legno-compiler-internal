#include "AnalogLib.h"

Fabric::Chip::Tile::Tile (
	Chip * parentChip,
	tileRow tileRowId,
	tileCol tileColId,
	unsigned char spiSSPin,
	unsigned char spiMisoPin,
	unsigned char ardAnaDiffChanBase
) :
	parentChip (parentChip),
	tileRowId (tileRowId),
	tileColId (tileColId),
	spiSSPin (spiSSPin),
	spiMisoPin (spiMisoPin)
{
  Serial.print("allocating tile ");
  Serial.print(tileRowId);
  Serial.print(", ");
  Serial.println(tileColId);
	pinMode(spiSSPin, OUTPUT);
	digitalWrite (spiSSPin, HIGH);
	pinMode(spiMisoPin, INPUT);

	slices = new Slice[4] {
		Slice (this, slice0, 12), // dummy ardAnaDiffChan
		Slice (this, slice1, 12),
		Slice (this, slice2, ardAnaDiffChanBase+2), // 6 and 2
		Slice (this, slice3, ardAnaDiffChanBase+0)  // 4 and 0
	};
}

Fabric::Chip::Tile::~Tile() { delete[] slices; };

void Fabric::Chip::Tile::defaults() {
	slices[0].defaults();
	slices[1].defaults();
	slices[2].defaults();
	slices[3].defaults();
	return true;
};


bool Fabric::Chip::Tile::calibrate () const {
	SerialUSB.println("Calibrating Slice 0");
	slices[0].calibrate();
	SerialUSB.println("Calibrating Slice 1");
	slices[1].calibrate();
	SerialUSB.println("Calibrating Slice 2");
	slices[2].calibrate();
	SerialUSB.println("Calibrating Slice 3");
	slices[3].calibrate();
	return true;
};

/*Internal function*/
void Fabric::Chip::Tile::controllerHelperTile (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<7||11<selLine) error ("selLine out of bounds");
	if (cfgTile<0||255<cfgTile) error ("cfgTile out of bounds");
	/*if arduino form, check that sram vector fields are within bounds*/
	// should only be used by controller and lut param writes
	// Serial.print("vec.tileRowId = "); Serial.println(vec.tileRowId);
	// Serial.print("vec.tileColId = "); Serial.println(vec.tileColId);
	// Serial.print("vec.selRow = "); Serial.println(vec.selRow);
	// Serial.print("vec.selCol = "); Serial.println(vec.selCol);
	// Serial.print("vec.cfgTile = "); Serial.println(vec.cfgTile);
	spiDriveTile ( 8, 0, selLine, cfgTile );
	spiDriveTile (noOp);
}

void Fabric::Chip::Tile::spiDriveTile (
	unsigned char selRow,
	unsigned char selCol,
	unsigned char selLine,
	unsigned char cfgTile
) const {
	digitalWriteDirect (spiSSPin, LOW);
	spiDrive ( selRow, selCol, selLine, cfgTile );
	digitalWriteDirect (spiSSPin, HIGH);
}

int Fabric::Chip::Tile::spiDriveTile ( const bool * vector ) const {
	digitalWriteDirect (spiSSPin, LOW);
	// Serial.print("spiMisoPin = "); Serial.println(spiMisoPin);
	unsigned int result = spiDrive ( vector, spiMisoPin );
	// Serial.print("result = "); Serial.println(result);
	digitalWriteDirect (spiSSPin, HIGH);
	return result;
}
