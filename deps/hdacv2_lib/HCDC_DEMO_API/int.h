typedef enum {
	mGainMRng = 0, /* -2 to 2  uA input, gain = 1,   -2 to 2  uA output*/
	mGainLRng = 1, /*-.2 to .2 uA input, gain = 1,  -.2 to .2 uA output*/
	mGainHRng = 2, /*-20 to 20 uA input, gain = 1,  -20 to 20 uA output*/
	hGainHRng = 3, /* -2 to 2  uA input, gain = 10, -20 to 20 uA output*/
	hGainMRng = 4, /*-.2 to .2 uA input, gain = 10,  -2 to 2  uA output*/
	lGainLRng = 5, /* -2 to 2  uA input, gain = .1, -.2 to .2 uA output*/
	lGainMRng = 6  /*-20 to 20 uA input, gain = .1,  -2 to 2  uA output*/
} intRange;

class Fabric::Chip::Tile::Slice::Integrator : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
		void setEnable ( bool enable ) override;
		void setInitialCode (
			unsigned char initialCode // fixed point representation of desired initial condition
			// 0 to 255 are valid
		);
    bool setInitialDirect (
                     float initial, // floating point representation of desired initial condition
                     bool hirange, // -1.0 to 1.0 are valid
                     bool setBias
                     );
    bool setInitial (
			float initial // floating point representation of desired initial condition
			// -10.0 to 10.0 are valid
		);
		void setException (
			bool exception // turn on overflow detection
			// turning false overflow detection saves power if it is known to be unnecessary
		);
		bool getException() const;
	private:
		class IntegratorInterface;
		class IntegratorIn;
		class IntegratorOut;
		Integrator (Slice * parentSlice);
		~Integrator () override { delete in0; delete out0; };
		bool calibrate ();
		bool calibrateTarget (
			bool hiRange,
			float initial
		);
		/*Set enable, invert, range*/
		void setParam0 () const override;
		/*Set calIc, overflow enable*/
		void setParam1 () const override;
		/*Set initial condition*/
		void setParam2 () const override;
		/*Set calOutOs, calOutEn*/
		void setParam3 () const override;
		/*Set calInOs, calInEn*/
		void setParam4 () const override;
		void setParam5 () const override {};
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
		const unsigned char anaIrefPmos = 5; /*5*/
		unsigned char initialCode = 0; // fixed point representation of initial condition
		bool exception = false; // turn on overflow detection
};

class Fabric::Chip::Tile::Slice::Integrator::IntegratorInterface : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface {
	friend Integrator;

	private:
		IntegratorInterface (Integrator * parentFu, ifc ifcId) : Interface(parentFu, ifcId), parentIntegrator(parentFu) {};
		void calibrate() override;
		const Integrator * const parentIntegrator;
};

class Fabric::Chip::Tile::Slice::Integrator::IntegratorIn : public Fabric::Chip::Tile::Slice::Integrator::IntegratorInterface {
	friend Integrator;

	public:
		void setRange (
			bool loRange, // 0.2uA mode
			bool hiRange // 20 uA mode
			// not both of the range settings should be true
			// default is 2uA mode
			// this setting should match the unit that gives the input to the integrator
		) override;
	private:
		IntegratorIn (Integrator * parentFu) : IntegratorInterface(parentFu, in0Id) {};
};

class Fabric::Chip::Tile::Slice::Integrator::IntegratorOut : public Fabric::Chip::Tile::Slice::Integrator::IntegratorInterface {
	friend Integrator;

	public:
		void setInv ( bool inverse ) override; // whether output is negated
		void setRange (
			bool loRange, // 0.2uA mode
			bool hiRange // 20 uA mode
			// not both of the range settings should be true
			// default is 2uA mode
			// this setting should match the unit that gives the input to the integrator
		) override;
	private:
		IntegratorOut (Integrator * parentFu) : IntegratorInterface(parentFu, out0Id) {};
};
