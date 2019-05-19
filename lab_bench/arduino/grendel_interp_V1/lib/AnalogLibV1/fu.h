#ifndef FU_BASECLASS
#define FU_BASECLASS
/*Valid options for functional unit interface.*/
// the order actually really matters here
typedef enum {
	in0Id,
	in1Id,
	out0Id,
	out1Id,
	out2Id
} ifc;

/*signal range configuration*/

typedef enum {
	mulMid = 0, /* -2 to 2  uA*/
	mulLo = 1,  /*-.2 to .2 uA*/
	mulHi = 2,  /*-20 to 20 uA*/
} mulRange;

typedef enum {
  RANGE_HIGH,
  RANGE_MED,
  RANGE_LOW,
  RANGE_UNKNOWN
} range_t;

typedef enum {
  DSRC_MEM,
  DSRC_EXTERN,
  DSRC_LUT0,
  DSRC_LUT1
} dac_source_t;

typedef enum {
  LSRC_ADC0,
  LSRC_ADC1,
  LSRC_EXTERN,
  LSRC_CONTROLLER,
} lut_source_t;

typedef struct {
  bool test_en;
  bool test_adc;
  bool test_i2v;
  bool test_rs;
  bool test_rsinc;
  bool enable;
  uint8_t pmos;
  uint8_t nmos;
  uint8_t pmos2;
  uint8_t i2v_cal;
  uint8_t upper_fs;
  uint8_t upper;
  uint8_t lower_fs;
  uint8_t lower;
  range_t range;
  uint8_t padding;
} adc_code_t;

typedef struct {
  bool vga;
  bool enable;
  bool inv[3];
  range_t range[3];
  uint8_t pmos;
  uint8_t nmos;
  uint8_t port_cal[3];
  uint8_t gain_cal;
  uint8_t gain_code;
  float gain_val;
} mult_code_t;


typedef struct {
  bool enable;
  bool inv;
  range_t range;
  dac_source_t source;
  uint8_t pmos;
  uint8_t nmos;
  uint8_t gain_cal;
  uint8_t const_code;
  float const_val;
} dac_code_t;

typedef struct {
  bool cal_enable[3];
  bool inv[3];
  bool enable;
  bool exception;
  range_t range[3];
  uint8_t pmos;
  uint8_t nmos;
  uint8_t gain_cal;
  uint8_t ic_code;
  uint8_t port_cal[3];
  float ic_val;
} integ_code_t;


typedef struct {
  uint8_t pmos;
  uint8_t nmos;
  range_t range[5];
  uint8_t port_cal[5];
  bool inv[5];
  bool enable;
  bool third;
} fanout_code_t;

typedef struct {
  lut_source_t source;
} lut_code_t;

typedef union {
  lut_code_t lut;
  fanout_code_t fanout;
  dac_code_t dac;
  adc_code_t adc;
  mult_code_t mult;
  integ_code_t integ;
  unsigned char charbuf[24];
} block_code_t;

typedef enum {
  MEAS_CHIP_OUTPUT,
  MEAS_ADC
} meas_method_t;

namespace util {

#define MAX_KEYS 25

  typedef struct {
    float bias[MAX_KEYS];
    float noise[MAX_KEYS];
    float target[MAX_KEYS];
    unsigned char size;
    unsigned char port[MAX_KEYS];
  } calib_result_t;

  typedef union {
    calib_result_t result;
    unsigned char charbuf[328];
  } ser_calib_result_t;


  void print_result(calib_result_t& result, int level);

  void init_result(calib_result_t& result);
  void add_prop(calib_result_t& result,
                ifc prop, float target, float bias, float noise);


  const char * ifc_to_string(ifc id);

  float range_to_coeff(range_t range);
  void save_conns(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                  int& n,
                  int n_max);

  float meas_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu);
  void meas_dist_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu, float& mean, float& variance);
}

namespace binsearch {
  bool find_bias_and_nmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                          float target,
                          const float max_error,
                          unsigned char & code,
                          unsigned char & nmos,
                          float & delta,
                          meas_method_t method
     );
  void find_bias(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                 float target,
                 unsigned char & code,
                 float & error,
                 meas_method_t method);

  float get_bias(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                float target,
                meas_method_t method);
  void test_stab(unsigned char code,
                 float error,
                 const float max_error,
                 bool& calib_failed);
  void test_iref(unsigned char code);
  bool is_valid_iref(unsigned char code);

}
class Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;
	friend Connection;
	friend Vector;

	public:
		class Interface;
		virtual void setEnable ( bool enable ) { error("setEnable not implemented"); };
		void setParallelOut ( bool onOff ) const;
		Interface * in0;
		Interface * in1;
		Interface * out0;
		Interface * out1;
		Interface * out2;

    virtual void setAnaIrefNmos () const {
			error("setAnaIrefNmos not implemented");
		};
		virtual void setAnaIrefPmos () const {
			error("setAnaIrefPmos not implemented");
		};

    Fabric* getFabric(){
      return parentSlice->parentTile->parentChip->parentFabric;
    }
    Fabric::Chip* getChip(){
      return parentSlice->parentTile->parentChip;
    }
    void updateFu();

	private:
		class GenericInterface;
		FunctionUnit (
			Slice * parentSlice_,
			unit unitId_
		) :
			parentSlice(parentSlice_),
			unitId(unitId_)
		{
    };

		virtual ~FunctionUnit () {};
		virtual void setParam0 () const { error("setParam0 not implemented"); };
		virtual void setParam1 () const { error("setParam1 not implemented"); };
		virtual void setParam2 () const { error("setParam2 not implemented"); };
		virtual void setParam3 () const { error("setParam3 not implemented"); };
		virtual void setParam4 () const { error("setParam4 not implemented"); };
		virtual void setParam5 () const { error("setParam5 not implemented"); };

		const Slice * const parentSlice;
		// used for gain and initial condition range calibration
		const unit unitId;
};

class Fabric::Chip::Tile::Slice::FunctionUnit::Interface {
	friend FunctionUnit;
	friend ChipAdc;
	friend Dac;
	friend Fanout;
	friend Integrator;
	friend Multiplier;
	friend Connection;
	friend Vector;

	public:
		virtual void setInv (
			bool inverse
		) {
			error("setInv not implemented");
		}; // whether output is negated
		virtual void setRange (range_t range) {
			error("setRange not implemented");
		};
		virtual ~Interface () {};
    FunctionUnit * const parentFu;
		const ifc ifcId;
		Interface * userSourceDest = NULL;
	private:
		Interface (
			FunctionUnit * parentFu,
			ifc ifcId
		) :
			parentFu(parentFu),
			ifcId(ifcId)
		{};
    // TODO: incomplete implementation because multiple sources possible

};

class Fabric::Chip::Tile::Slice::FunctionUnit::GenericInterface : public Fabric::Chip::Tile::Slice::FunctionUnit::Interface {
	friend ChipInput;
	friend ChipOutput;
	friend TileInOut;
	friend Fanout;
	friend Integrator;

	private:
		GenericInterface (
			FunctionUnit * parentFu_,
			ifc ifcId_
		) :
			Interface (parentFu_, ifcId_)
		{};
};

#endif
