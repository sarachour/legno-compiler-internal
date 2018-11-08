class Fabric::Chip::Tile::Slice::ChipInput : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
		void setEnable ( bool enable ) const {
			if (
				parentSlice->parentTile->tileRowId==tileRow1 && 
				parentSlice->parentTile->tileColId==tileCol1
			){
				if ( parentSlice->parentTile->parentChip->chipColId==chipCol0 ) {
					if ( parentSlice->sliceId==slice2 ) {
						digitalWrite( 26, enable?HIGH:LOW );
					} else if ( parentSlice->sliceId==slice3 ) {
						digitalWrite( 27, enable?HIGH:LOW );
					}
				} else {
					if ( parentSlice->sliceId==slice2 ) {
						digitalWrite( 28, enable?HIGH:LOW );
					} else if ( parentSlice->sliceId==slice3 ) {
						digitalWrite( 29, enable?HIGH:LOW );
					}
				}
			}
		};

	private:
		ChipInput (
			Slice * parentSlice
		) :
			FunctionUnit(parentSlice, chipInp)
		{
			out0 = new GenericInterface (this, out0Id);
			tally_dyn_mem <GenericInterface> ("GenericInterface");
			/*ANALOG INPUT CHANNEL ENABLE PINS*/
		};
		~ChipInput () override { delete out0; };
};

// const float resistorValue = 600000.0;
// const float fullScaleCurrent = 0.000001861;

class Fabric::Chip::Tile::Slice::ChipOutput : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
	/*Measure the reading of an ADC from multiple samples*/
	/*Measure the differential voltage from a pair of ADC from multiple samples*/
	float analogAvg ( unsigned int samples ) const;

	private:
		ChipOutput (
			Slice * parentSlice,
			unsigned char ardAnaDiffChan
		) :
			FunctionUnit(parentSlice, chipOut),
			ardAnaDiffChan (ardAnaDiffChan)
		{
			in0 = new GenericInterface (this, in0Id);
			tally_dyn_mem <GenericInterface> ("GenericInterface");
		};
		~ChipOutput () override { delete in0; };

		const unsigned char ardAnaDiffChan;
};
