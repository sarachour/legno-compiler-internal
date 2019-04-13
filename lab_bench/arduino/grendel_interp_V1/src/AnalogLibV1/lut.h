extern const bool noOp[];

typedef enum {
	ns1_0 = 0, /*delay lines for read = 1ns*/
	ns1_5 = 1, /*delay lines for read = 1.5ns*/
	ns2_0 = 2, /*delay lines for read = 2ns*/
	ns2_5 = 3  /*delay lines for read = 2.5ns*/
} lutRDelay;

typedef enum {
	ps550	= 0, /*delay lines for write = 550ps*/
	ps1060	= 1  /*delay lines for write = 1.06ns*/
} lutWDelay;

typedef enum {
	ns_3 =	0, /*3ns is the default*/
	ns_6 =	1  /*6ns trigger delay*/
} lutTrigDelay;

typedef enum {
	adcL	= 0, /*signals from adcL are selected*/
	adcR	= 1, /*signals from adcR are selected*/
	extLut	= 2, /*signals from external are selected*/
	ctlrLut	= 3  /*signals from controller are selected*/
} lutSel;

class Fabric::Chip::Tile::Slice::LookupTable : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
		void setSource (
			bool external, // lut takes input from chip parallel input
			bool adc0, // lut takes input from first analog to digital converter
			bool adc1 // lut takes input from second analog to digital converter
			// only one of these should be true
		);
		/*Set LUT SRAM contents*/
		void setLut (
			unsigned char addr,
			unsigned char data
		) const;
		/*Put LUT in writing mode*/
		void setStart () const;
		/*Remove LUT in writing mode*/
		// void setStop ();
	private:
		LookupTable (
			Slice * parentSlice
		) :
			FunctionUnit(parentSlice, unitLut),
			parentSlice(parentSlice)
		{};
		/*Set read delay, write delay, clock select, input select*/
		void setParam0 (
			lutTrigDelay trigDelay, /*Trigger output delay*/
			lutRDelay rDelay, /*pins for programming the delay lines for read operation*/
			lutWDelay wDelay, /*pin for programming the delay lines for write operation*/
			lutSel selClk, /*clock signal selection*/
			lutSel selIn /*input signal selection*/
		) const;
		/*Helper function*/
		void setParamHelper (
			unsigned char selLine,
			unsigned char cfgTile
		) const;
		bool external = false;
		bool adc0 = false;
		bool adc1 = false;
		const Slice * const parentSlice;
};