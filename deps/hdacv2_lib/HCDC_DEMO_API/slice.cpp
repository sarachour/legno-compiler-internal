#include "HCDC_DEMO_API.h"
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

bool Fabric::Chip::Tile::Slice::calibrate () const {

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
			if (!adc->calibrate()) return false;
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
                        if (!adc->calibrate()) return false;
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
                        if (!adc->calibrate()) return false;
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
                        if (!adc->calibrate()) return false;
		}
		// if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==5) {

		//if (sliceId==slice0 || sliceId==slice2) {
        //               if (!adc->calibrate()) return false;
		//}
		// if (!dac->findBiasAdc (dac->negGainCalCode)) return false;

	} else if (HCDC_DEMO_BOARD==6){
    if (sliceId==slice0 || sliceId==slice2) {
			if (
          sliceId==slice0
          && parentTile->tileRowId==tileRow0
          && parentTile->tileColId==tileCol0
          && parentTile->parentChip->chipRowId==chipRow0
          && parentTile->parentChip->chipColId==chipCol0
          ) SerialUSB.println("SKIPPING THIS ADC");
			else
        if (!adc->calibrate()) return false;
		}
  }
  else {
		error("HCDC_DEMO_BOARD # not recognized. Only [1-6] are valid.");
	}

	SerialUSB.println("Calibrating DAC");
	if (!dac->calibrate()) return false;
	SerialUSB.println("Calibrating Fanout 0");
	if (!fans[0].calibrate()) return false;
	SerialUSB.println("Calibrating Fanout 1");
	if (!fans[1].calibrate()) return false;
	SerialUSB.println("Calibrating Multiplier 0");
	if (!muls[0].calibrate()) return false;
	SerialUSB.println("Calibrating Multiplier 1");
	if (!muls[1].calibrate()) return false;
	SerialUSB.println("Calibrating Integrator");
	if (!integrator->calibrate()) return false;
	return true;

}
