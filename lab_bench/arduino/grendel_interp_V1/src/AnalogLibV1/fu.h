/*Valid options for functional unit interface.*/
typedef enum {
	in0Id,
	in1Id,
	out0Id,
	out1Id,
	out2Id
} ifc;

/*signal range configuration*/
typedef enum {
	fanLo = 0, /*2uA & 200nA*/
 	fanMid = 0, /*2uA & 200nA*/
	fanHi = 1 /*20uA*/
} fanRange;

typedef enum {
	mulMid = 0, /* -2 to 2  uA*/
	mulLo = 1,  /*-.2 to .2 uA*/
	mulHi = 2,  /*-20 to 20 uA*/
} mulRange;

class Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;
	friend Connection;
	friend Vector;

	public:
		class Interface;
		virtual void setEnable ( bool enable ) { error("not implemented"); };
		void setParallelOut ( bool onOff ) const;
		Interface * in0;
		Interface * in1;
		Interface * out0;
		Interface * out1;
		Interface * out2;
	private:
		class GenericInterface;
		FunctionUnit (
			Slice * parentSlice_,
			unit unitId_
		) :
			parentSlice(parentSlice_),
			unitId(unitId_)
		{};
		virtual ~FunctionUnit () {};
		virtual void setParam0 () const { error("not implemented"); };
		virtual void setParam1 () const { error("not implemented"); };
		virtual void setParam2 () const { error("not implemented"); };
		virtual void setParam3 () const { error("not implemented"); };
		virtual void setParam4 () const { error("not implemented"); };
		virtual void setParam5 () const { error("not implemented"); };
		bool findBiasHelper (
			float target,
			unsigned char & code
		);
		void binarySearchTarget (
			float target,
			unsigned char minCode,
			float minBest,
			unsigned char maxCode,
			float maxBest,
			unsigned char & finalCode
		) const;
		bool binarySearchAvg (
			unsigned char minGainCode,
			float minBest,
			unsigned char maxGainCode,
			float maxBest,
			unsigned char & finalGainCode
		) const;
		float binarySearchMeas () const;
		bool setAnaIrefDacNmosHelper (
			bool decrement,
			bool increment
		);

		virtual bool setAnaIrefDacNmos (
			bool decrement,
			bool increment
		) {
			error("not implemented");
			return false;
		};
		virtual void setAnaIrefPmos () const {
			error("not implemented");
		};

		const Slice * const parentSlice;
		// used for gain and initial condition range calibration
		const unit unitId;
		bool enable = false;
	public:
		unsigned char negGainCalCode = 0;
		unsigned char anaIrefDacNmos = 0;
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
			error("not implemented");
		}; // whether output is negated
		virtual void setRange (
			bool loRange,
			bool hiRange
		) {
			error("not implemented");
		};
		virtual ~Interface () {};
	private:
		Interface (
			FunctionUnit * parentFu,
			ifc ifcId
		) :
			parentFu(parentFu),
			ifcId(ifcId)
		{};
		virtual void calibrate() {
			error("not implemented");
		};
		virtual bool findBias (
			unsigned char & offsetCode
		) {
			error("not implemented");
			return false;
		};
		bool findBiasHelper (
			unsigned char & code
		) const;
		virtual void binarySearch (
			unsigned char minCode,
			float minBest,
			unsigned char maxCode,
			float maxBest,
			unsigned char & finalCode
		) const;
		bool binarySearchAvg (
			unsigned char minGainCode,
			float minBest,
			unsigned char maxGainCode,
			float maxBest,
			unsigned char & finalGainCode
		) const;
		float binarySearchMeas () const;
		FunctionUnit * const parentFu;
		const ifc ifcId;
		Interface * userSourceDest = NULL; // TODO: incomplete implementation because multiple sources possible

		bool inverse = false;

		bool loRange = false;
		bool hiRange = false;
	public:
		unsigned char loOffsetCode = 31;
		unsigned char midOffsetCode = 31;
		unsigned char hiOffsetCode = 31;
		bool calEn = false; /*Set high to configure integrator for output offset calibration*/
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
