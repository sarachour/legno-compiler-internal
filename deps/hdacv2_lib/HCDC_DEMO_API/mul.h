class Fabric::Chip::Tile::Slice::Multiplier : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;
	public:
		void setEnable ( bool enable ) override;
		void setGainCode (
			unsigned char gainCode // fixed point representation of desired gain
			// 0 to 255 are valid
		);
		bool setGain (
			float gain // floating point representation of desired gain
			// -100.0 to 100.0 are valid
		);
		void setVga (
			bool vga // constant coefficient multiplier mode
		);
	private:
		class MultiplierInterface;
		Multiplier (Slice * parentSlice, unit unitId);
		~Multiplier () override {
			delete out0;
			delete in0;
			delete in1;
		};
		bool calibrate ();
		bool calibrateTarget (
			bool hiRange,
			float gain
		);
		/*Set enable, input 1 range, input 2 range, output range*/
		void setParam0 () const override;
		/*Set calDac, enable variable gain amplifer mode*/
		void setParam1 () const override;
		/*Set gain if VGA mode*/
		void setParam2 () const override;
		/*Set calOutOs*/
		void setParam3 () const override;
		/*Set calInOs1*/
		void setParam4 () const override;
		/*Set calInOs2*/
		void setParam5 () const override;
		/*Helper function*/
		void setParamHelper (
			unsigned char selLine,
			unsigned char cfgTile
		) const;
		bool setAnaIrefDacNmos (
			bool decrement,
			bool increment
		) override;
		void setAnaIrefPmos () const override;
		bool vga = false;
		unsigned char gainCode = 128;
	public:
		unsigned char anaIrefPmos = 3;
};

class Fabric::Chip::Tile::Slice::Multiplier::MultiplierInterface : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface  {
	friend Multiplier;
	public:
		void setRange (
			bool loRange, // 0.2uA mode
			bool hiRange // 20 uA mode
			// default is 2uA mode
			// this setting should match the unit that gives the input to the multiplier
		) override;
	private:
		MultiplierInterface (Multiplier * parentFu, ifc ifcId) : Interface(parentFu, ifcId), parentMultiplier(parentFu) {};
		void calibrate () override;
		Multiplier * const parentMultiplier;
};