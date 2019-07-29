#include "AnalogLib.h"
extern const char HCDC_DEMO_BOARD;

Fabric::Chip::Tile::Slice::Slice (
	Chip::Tile * parentTile,
	slice sliceId,
	unsigned char ardAnaDiffChan
) :
	parentTile (parentTile),
	sliceId (sliceId),
	ardAnaDiffChan (ardAnaDiffChan)
{
  Serial.print("allocating slice ");
  Serial.println(sliceId);
	chipInput = new ChipInput (this);
	tally_dyn_mem <ChipInput> ("ChipInput");

	tileInps = new TileInOut[4] {
		TileInOut(this, tileInp0),
		TileInOut(this, tileInp1),
		TileInOut(this, tileInp2),
		TileInOut(this, tileInp3)
	};
	tally_dyn_mem <TileInOut[4]> ("TileInOut[4]");

	muls = new Multiplier[2] {
		Multiplier (this, unitMulL),
		Multiplier (this, unitMulR)
	};
	tally_dyn_mem <Multiplier[2]> ("Multiplier[2]");

	dac = new Dac (this);
	tally_dyn_mem <Dac> ("Dac");

	integrator = new Integrator (this);
	tally_dyn_mem <Integrator> ("Integrator");

	fans = new Fanout[2] {
		Fanout (this, unitFanL),
		Fanout (this, unitFanR)
	};
	tally_dyn_mem <Fanout[2]> ("Fanout[2]");

	if (sliceId==slice0 || sliceId==slice2) {
		adc = new ChipAdc (this);
		tally_dyn_mem <ChipAdc> ("ChipAdc");
		lut = new LookupTable (this);
		tally_dyn_mem <LookupTable> ("LookupTable");
	}

	tileOuts = new TileInOut[4] {
		TileInOut(this, tileOut0),
		TileInOut(this, tileOut1),
		TileInOut(this, tileOut2),
		TileInOut(this, tileOut3)
	};
	tally_dyn_mem <TileInOut[4]> ("TileInOut[4]");

	chipOutput = new ChipOutput (this, ardAnaDiffChan);
	tally_dyn_mem <ChipOutput> ("ChipOutput");
  Serial.println("allocated slice");
}

Fabric::Chip::Tile::Slice::~Slice () {
	delete chipInput;
	delete[] tileInps;
	delete dac;
	delete[] muls;
	delete integrator;
	delete[] fans;
	if (sliceId==slice0 || sliceId==slice2) {
		delete adc;
		delete lut;
	}
	delete[] tileOuts;
	delete chipOutput;
};
int slice_to_int(const slice slc){
  switch(slc){
  case slice0: return 0; break;
  case slice1: return 1; break;
  case slice2: return 2; break;
  case slice3: return 3; break;
  }
}
bool Fabric::Chip::Tile::Slice::calibrateTarget () const {
	print_log("Calib.TARGET DAC");
  Serial.flush();
	if (!dac->calibrateTarget(prof::TEMP,0.01)) return false;
	print_log("Calib.TARGET Multiplier 0");
  Serial.flush();
	if (!muls[0].calibrateTarget(prof::TEMP,0.01)) return false;
	print_log("Calib.TARGET Multiplier 1");
  Serial.flush();
	if (!muls[1].calibrateTarget(prof::TEMP,0.01)) return false;
	print_log("Calib.TARGET Integrator");
  Serial.flush();
	if (!integrator->calibrateTarget(prof::TEMP,0.01)) return false;
	print_log("Done");
  Serial.flush();
	return true;

}
void Fabric::Chip::Tile::Slice::defaults () {
  dac->defaults();
	fans[0].defaults();
	fans[1].defaults();
  muls[0].defaults();
  muls[1].defaults();
  integrator->defaults();

  if (sliceId == slice0 || sliceId == slice2) {
    adc->defaults();
    lut->defaults();
  }
}
bool Fabric::Chip::Tile::Slice::calibrate () const {

  print_log("Calibrating ADC");
  Serial.flush();
	if (HCDC_DEMO_BOARD==1) {

		if (sliceId==slice0 || sliceId==slice2) {
			if (
				sliceId==slice2
				&& parentTile->tileRowId==tileRow0
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol0
			) SerialUSB.println("SKIPPING THIS ADC");
			else
			if (!adc->calibrate(prof::TEMP,0.01)) return false;
		}
		// if (
		// 	sliceId==slice2
		// 	&& parentTile->tileRowId==tileRow0
		// 	&& parentTile->tileColId==tileCol1
		// 	&& parentTile->parentChip->chipRowId==chipRow0
		// 	&& parentTile->parentChip->chipColId==chipCol0
                // ) SerialUSB.println("SKIPPING THIS DAC");
		// else if (
		// 	sliceId==slice3
		// 	&& parentTile->tileRowId==tileRow0
		// 	&& parentTile->tileColId==tileCol1
		// 	&& parentTile->parentChip->chipRowId==chipRow0
		// 	&& parentTile->parentChip->chipColId==chipCol0
                // ) SerialUSB.println("SKIPPING THIS DAC");
		// else if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==2) {

		if (sliceId==slice0 || sliceId==slice2) {
			if (
				sliceId==slice0
				&& parentTile->tileRowId==tileRow1
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol0
                        ) SerialUSB.println("SKIPPING THIS ADC");
			else if (
				sliceId==slice0
				&& parentTile->tileRowId==tileRow0
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol0
                        ) SerialUSB.println("SKIPPING THIS ADC");
			else
                        if (!adc->calibrate(prof::TEMP,0.01)) return false;
		}
		// if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==3) {

		if (sliceId==slice0 || sliceId==slice2) {
			if (
				sliceId==slice0
				&& parentTile->tileRowId==tileRow1
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol0
                        ) SerialUSB.println("SKIPPING THIS ADC");
			else if (
				sliceId==slice2
				&& parentTile->tileRowId==tileRow1
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol0
                        ) SerialUSB.println("SKIPPING THIS ADC");
			else
                        if (!adc->calibrate(prof::TEMP,0.01)) return false;
		}
		// if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==4) {

		if (sliceId==slice0 || sliceId==slice2) {
			if (
				sliceId==slice0
				&& parentTile->tileRowId==tileRow0
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol0
                        ) SerialUSB.println("SKIPPING THIS ADC");
			else if (
				sliceId==slice0
				&& parentTile->tileRowId==tileRow1
				&& parentTile->tileColId==tileCol1
				&& parentTile->parentChip->chipRowId==chipRow0
				&& parentTile->parentChip->chipColId==chipCol1
                        ) SerialUSB.println("SKIPPING THIS ADC");
			else
                        if (!adc->calibrate(prof::TEMP,0.01)) return false;
		}
		// if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==5) {

		//if (sliceId==slice0 || sliceId==slice2) {
        //               if (!adc->calibrate(prof::TEMP,)) return false;
		//}
		// if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==6) {
    if (sliceId == slice0 || sliceId == slice2) {
      if (!adc->calibrate(prof::TEMP,0.01)) return false;
    }
  }
  else {
		error("HCDC_DEMO_BOARD # not recognized. Only 1,2,3,4,5 are valid.");
	}
	print_log("Calibrating DAC");
	if (!dac->calibrate(prof::TEMP,0.01)) return false;
	print_log("Calibrating Fanout 0");
	if (!fans[0].calibrate(prof::TEMP,0.01)) return false;
	print_log("Calibrating Fanout 1");
	if (!fans[1].calibrate(prof::TEMP,0.01)) return false;
  print_log("Calibrating Multiplier 0");
	if (!muls[0].calibrate(prof::TEMP,0.01)) return false;
	print_log("Calibrating Multiplier 1");
	if (!muls[1].calibrate(prof::TEMP,0.01)) return false;
	print_log("Calibrating Integrator");
	if (!integrator->calibrate(prof::TEMP,0.01)) return false;
	print_log("Done");
	return true;

}
