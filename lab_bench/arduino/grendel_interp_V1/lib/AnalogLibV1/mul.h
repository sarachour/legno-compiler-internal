#ifndef MUL_H
#define MUL_H

#include "fu.h"

class Fabric::Chip::Tile::Slice::Multiplier : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;
	public:
		void setEnable ( bool enable ) override;
		void setGainCode (
			unsigned char gainCode // fixed point representation of desired gain
			// 0 to 255 are valid
		);
    bool setGain(float gain);
		void setVga (
			bool vga // constant coefficient multiplier mode
		);

    mult_code_t m_codes;
    void update(mult_code_t codes);
    void defaults();
    void characterize(util::calib_result_t& result);
    bool calibrate (util::calib_result_t& result,
                    const float max_error);
		bool calibrateTarget(util::calib_result_t& result,
                         const float max_error);
	private:
    void measure_vga(util::calib_result_t& result,
                     float in0);
    void measure_mult(util::calib_result_t& result,
                      float in0,float in1);


		class MultiplierInterface;
		Multiplier (Slice * parentSlice, unit unitId);
		~Multiplier () override {
			delete out0;
			delete in0;
			delete in1;
		};
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
		void setAnaIrefNmos () const override;
		void setAnaIrefPmos () const override;
		//bool vga = false;
		//unsigned char gainCode = 128;
	public:
		//unsigned char anaIrefPmos = 3;
};

class Fabric::Chip::Tile::Slice::Multiplier::MultiplierInterface : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface  {
	friend Multiplier;
	public:
		void setRange (range_t range) override;
	private:
		MultiplierInterface (Multiplier * parentFu, ifc ifcId) : Interface(parentFu, ifcId), parentMultiplier(parentFu) {};
		Multiplier * const parentMultiplier;
};

#endif
