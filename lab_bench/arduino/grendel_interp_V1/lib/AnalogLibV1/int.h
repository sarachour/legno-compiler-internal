#ifndef INTEG_H
#define INTEG_H

#include "fu.h"
#include "profile.h"

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
    bool setInitial(float initial);
		void setException (
			bool exception // turn on overflow detection
			// turning false overflow detection saves power if it is known to be unnecessary
		);
		bool getException() const;
    void setInv (ifc port, bool inverse ); // whether output is negated
		void setRange (ifc port, range_t range);
    void update(integ_code_t codes);
    integ_code_t m_codes;
		bool calibrateTarget (profile_t& result,
                          const float max_error);
		bool calibrate (profile_t& result,
                    const float max_error);
		void characterize(profile_t& result);
		void characterizeTarget(profile_t& result);
    void defaults();
	private:
		void measure(profile_t& result);
		Integrator (Slice * parentSlice);
		~Integrator () override { delete in0; delete out0; };
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
		void setAnaIrefNmos () const override;
		void setAnaIrefPmos () const override;
		//const unsigned char anaIrefPmos = 5; /*5*/
		//unsigned char initialCode = 0; // fixed point representation of initial condition
		//bool exception = false; // turn on overflow detection
};

#endif
