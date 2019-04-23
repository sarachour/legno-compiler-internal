typedef enum {
	// dacLo = 0,		/*the DAC block signal range is 2uA*/
	dacMid = 0,	/*the DAC block signal range is 2uA*/
	dacHi = 1		/*the DAC block signal range is 20uA*/
} dacRange;

typedef enum {
	lutL	= 0, /*signals from lutL are selected*/
	lutR	= 1, /*signals from lutR are selected*/
	extDac	= 2, /*signals from external are selected*/
	adc		= 3  /*signals from ADC are selected*/
} dacSel;

class Fabric::Chip::Tile::Slice::Dac : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
		void setEnable ( bool enable ) override;
		void setHiRange (
			// default is 2uA mode
			bool hiRange // 20 uA mode
		);
		void setSource (
			bool memory,
			bool external, // digital to analog converter takes input from chip parallel input
			bool lut0, // digital to analog converter takes input from first lookup table
			bool lut1 // digital to analog converter takes input from second lookup table
			// only one of these should be true
		);
		void setConstantCode (
			unsigned char constantCode // fixed point representation of desired constant
			// 0 to 255 are valid
		);
    bool setConstantDirect (
                      float constant, // floating point representation of desired constant
                      bool hiRange,
                      bool set_bias
                      // -10.0 to 10.0 are valid
    );
    bool setConstant (
			float constant // floating point representation of desired constant
			// -10.0 to 10.0 are valid
		);
	private:
		class DacOut;
		Dac (Slice * parentSlice);
		~Dac () override { delete out0; };
		/*Set enable, invert, range, clock select*/
		void setParam0 () const override;
		/*Set calDac, input select*/
		void setParam1 () const override;
		void setParamHelper (
			unsigned char selLine,
			unsigned char cfgTile
		) const;
		bool calibrate ();
		bool calibrateTarget (
			bool hiRange,
			float constant
		);
		bool setAnaIrefDacNmos (
			bool decrement,
			bool increment
		) override;
		void setAnaIrefPmos () const override {};

		bool findBiasAdc (
			unsigned char & gainCalCode
		);
		bool findBiasHelperAdc (
			unsigned char & code
		);
		void binarySearchAdc (
			unsigned char minGainCalCode,
			float minBest,
			unsigned char maxGainCalCode,
			float maxBest,
			unsigned char & finalGainCalCode
		);

		bool memory=false;
		bool external=false;
		bool lut0=false;
		bool lut1=false;
		unsigned char constantCode;
};

class Fabric::Chip::Tile::Slice::Dac::DacOut : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface  {
	friend Dac;

	public:
		void setInv ( bool inverse ) override; // whether output is negated
	private:
		DacOut (Dac * parentFu) : Interface(parentFu, out0Id) {};
};
