class Fabric::Chip::Tile::Slice::Fanout : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
		void setEnable ( bool enable ) override;
		void setRange (
			range_t range// 20uA mode
			// 20uA mode results in more ideal behavior in terms of phase shift but consumes more power
			// this setting should match the unit that gives the input to the fanout
		);
		void setThird (
			bool third // whether third output is on
		);
		bool calibrate ();

    fanout_code_t m_codes;
	private:
		class FanoutOut;
		Fanout (Slice * parentSlice, unit unitId);
		~Fanout () override {
			delete in0;
			delete out0;
			delete out1;
			delete out2;
		};
    void update(fanout_code_t codes){
      m_codes = codes;
      updateFu();
    }
		/*Set enable, range*/
		void setParam0 () const override;
		/*Set calDac1, invert output 1*/
		void setParam1 () const override;
		/*Set calDac2, invert output 2*/
		void setParam2 () const override;
		/*Set calDac3, invert output 3, enable output 3*/
		void setParam3 () const override;
		void setParam4 () const override {};
		void setParam5 () const override {};
		/*Helper function*/
		void setParamHelper (
			unsigned char selLine,
			unsigned char cfgTile
		) const;
		void setAnaIrefNmos () const override;
		void setAnaIrefPmos () const override;

		// generally does not influence fanout performance
		// anaIrefNmos is remapped in SW to anaIrefPmos
		// const unsigned char anaIrefPmos = 3;
};

class Fabric::Chip::Tile::Slice::Fanout::FanoutOut : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface  {
	friend Fanout;

	public:
		void setInv ( bool inverse ) override;
	private:
		FanoutOut (Fanout * parentFu, ifc ifcId) :
			Interface(parentFu, ifcId),
			parentFanout(parentFu)
		{};
		Fanout * const parentFanout;
};
