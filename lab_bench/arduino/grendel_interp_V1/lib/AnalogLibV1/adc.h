typedef enum {
	adcLo = 0,		/*2uA*/
	adcMid = 0,	/*2uA*/
	adcHi = 1		/*20uA*/
} adcRange;

typedef enum {
	ns11_5 =	0, /*11.5 ns delay (normal operation)*/
	ns9_7 = 	1, /*9.7 ns delay*/
	ns7_8 = 	2, /*7.8 ns delay*/
	ns5_8 = 	3  /*5.8 ns delay*/
} adcDelay;

typedef enum {
	ns3 =		0, /*3ns is the default*/
	ns6 =		1  /*6ns trigger delay*/
} adcTrigDelay;

typedef enum {
	nA100 = 0, /*IFS = 100nA*/
	nA200 = 1, /*IFS = 200nA*/
	nA300 = 2, /*IFS = 300nA*/
	nA400 = 3  /*IFS = 400nA*/
} adcCalCompFs;

class Fabric::Chip::Tile::Slice::ChipAdc : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;
	public:
		void setEnable ( bool enable ) override;
		void setHiRange (
			// default is 2uA mode
			bool hiRange // 20 uA mode
		);
		unsigned char getData () const;
		unsigned char getStatusCode() const;
		bool getException() const;
    unsigned char getCalCompLower(){
      return calCompLower;
    }
    unsigned char getCalCompLowerFS(){
      return calCompLowerFs;
    }
    unsigned char getCalCompUpper(){
      return calCompUpper;
    }
    unsigned char getCalCompUpperFS(){
      return calCompUpperFs;
    }
    unsigned char getI2VOffset(){
      return calI2V;
    }
    unsigned char getAnaIrefNmos(){
      return anaIrefDacNmos;
    }
    unsigned char getAnaIrefPmos1(){
      return anaIref1Pmos;
    }
    unsigned char getAnaIrefPmos2(){
      return anaIref2Pmos;
    }
	private:
		class AdcIn;
		ChipAdc (Slice * parentSlice);
		~ChipAdc () override { delete in0; };
		/*Set enable, range, delay, decRst*/
		void setParam0 () const override;
		/*Set calibration enable, calCompUpperEn, calIv*/
		void setParam1 () const override;
		/*Set calCompLower, calCompLowerFs*/
		void setParam2 () const override;
		/*Set calCompUpper, calCompUpperFs*/
		void setParam3 () const override;
		/*Set testEn, testAdc, testIv, testRs, testRsInc*/
		void setParam4 (
			bool testEn, /*Configure the entire block in testing mode so that I2V and A/D can be tested individually*/
			bool testAdc, /*Testing the ADC individually.*/
			bool testIv, /*Testing the I2V individually.*/
			bool testRs, /*Testing the rstring individually.*/
			bool testRsInc /*Configure the counter for upward or downward increments during set up for testing R-string separately (w/ cfgCalEN=1)*/
		) const;
		/*Helper function*/
		void setParamHelper (
			unsigned char selLine,
			unsigned char cfgTile
		) const;
		bool calibrate ();
		bool findCalCompFs ();
		bool checkScale ();
		bool checkSpread (
			unsigned char spread,
			bool lowerPos,
			bool upperPos
		);
		bool checkSteady (
			unsigned char dacCode
		) const;
		bool setAnaIrefDacNmos (
			bool decrement,
			bool increment
		) override;
		void setAnaIrefPmos () const override;

		unsigned char calI2V = 31;
		// anaIrefI2V is remapped in SW to AnaIrefDacNmos

		unsigned char calCompLower = 31;
		adcCalCompFs calCompLowerFs = nA100;
		const unsigned char anaIref1Pmos = 4;

		unsigned char calCompUpper = 31;
		adcCalCompFs calCompUpperFs = nA100;
		const unsigned char anaIref2Pmos = 4;
};

class Fabric::Chip::Tile::Slice::ChipAdc::AdcIn : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface {
	friend ChipAdc;

	public:
		void setRange (
			bool hiRange // 20uA mode
			// 20uA mode results in more ideal behavior in terms of phase shift but consumes more power // this setting should match the unit that gives the input to the fanout
		);
	private:
			AdcIn (ChipAdc * parentFu) :
			Interface(parentFu, in0Id),
			parentAdc(parentFu)
		{};
		bool findBias (
			unsigned char & offsetCode
		) override;
		void binarySearch (
			unsigned char minCode,
			float minBest,
			unsigned char maxCode,
			float maxBest,
			unsigned char & finalCode
		) const override;
		const ChipAdc * const parentAdc;
};
