class Fabric::Chip::Tile::Slice {
	friend Tile;
	friend Connection;
	friend Vector;

	public:
		class FunctionUnit;
		class ChipInput;
		class TileInOut;
		class Dac;
		class Multiplier;
		class Integrator;
		class Fanout;
		class ChipAdc;
		class LookupTable;
		class ChipOutput;

		ChipInput * chipInput;
		TileInOut * tileInps;
		Dac * dac;
		Multiplier * muls;
		Integrator * integrator;
		Fanout * fans;
		ChipAdc * adc;
		LookupTable * lut;
		TileInOut * tileOuts;
		ChipOutput * chipOutput;

    bool calibrate() const;
    bool calibrateTarget() const;

	private:
		Slice (
			Tile * parentTile,
			slice sliceId,
			unsigned char ardAnaDiffChan
		);
		~Slice ();
		Tile * const parentTile;
		const slice sliceId;
		/*ANALOG INPUT PINS*/
		const unsigned char ardAnaDiffChan; /*ANALOG OUTAna*/
};
