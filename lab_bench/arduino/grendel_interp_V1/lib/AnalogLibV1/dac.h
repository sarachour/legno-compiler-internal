#ifndef DAC_H
#define DAC_H

#include "fu.h"
#include "calib_util.h"

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




#define NCACHE_ELS 10
#define NCACHE_SLOTS 4


typedef struct {
  dac_code_t cache[NCACHE_SLOTS][NCACHE_ELS];
  bool is_cached[NCACHE_SLOTS][NCACHE_ELS];
  Fabric::Chip::Tile::Slice::Dac* owners[NCACHE_SLOTS];
  int lru_dac[NCACHE_SLOTS];
  int lru_val[NCACHE_SLOTS][NCACHE_ELS];
} dac_cache_t;

extern dac_cache_t DAC_CACHE;

float make_reference_dac(cutil::calibrate_t& calib,
                         dac_code_t& config,
                         Fabric::Chip::Tile::Slice::Dac* dac,
                         Fabric::Chip::Tile::Slice::Dac* ref_dac);

namespace dac_cache {

  void initialize();
  bool get_cached(Fabric::Chip::Tile::Slice::Dac* dac,
                    float value,
                    dac_code_t& this_code);
  void cache(Fabric::Chip::Tile::Slice::Dac* dac,
              float value,
              dac_code_t& this_code);

}
class Fabric::Chip::Tile::Slice::Dac : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	public:
		void setEnable ( bool enable ) override;
		void setRange (
			// default is 2uA mode
			range_t rng// 20 uA mode
		);
		void setSource (dac_source_t src);
		void setConstantCode (
			unsigned char constantCode // fixed point representation of desired constant
			// 0 to 255 are valid
		);
    bool setConstant (
			float constant // floating point representation of desired constant
			// -10.0 to 10.0 are valid
		);
    void update(dac_code_t codes);
    dac_code_t m_codes;
		void setInv (bool inverse ); // whether output is negated
    profile_t measure(float input);
    bool calibrate (profile_t& result,
                    const float max_error);
		bool calibrateTarget (profile_t& result,
                          const float max_error);
    void defaults();
	private:
		Dac (Slice * parentSlice);
		~Dac () override { delete out0; };
		/*Set enable, invert, range, clock select*/
		void setParam0 () const override;
		/*Set calDac, input select*/
		void setParam1 () const override;
    void setParam2 () const override {};
    void setParam3 () const override {};
    void setParam4 () const override {};
    void setParam5 () const override {};
		void setParamHelper (
			unsigned char selLine,
			unsigned char cfgTile
		) const;
		void setAnaIrefNmos () const override;
		void setAnaIrefPmos () const override {};

};


#endif
