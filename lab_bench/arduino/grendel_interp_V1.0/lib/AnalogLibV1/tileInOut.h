class Fabric::Chip::Tile::Slice::TileInOut : public Fabric::Chip::Tile::Slice::FunctionUnit {
	friend Slice;

	TileInOut ( Slice * parentSlice, unit unitId_ ) : FunctionUnit(parentSlice, unitId_) {
		in0 = new GenericInterface (this, in0Id);
		tally_dyn_mem <GenericInterface> ("GenericInterface");
		out0 = new GenericInterface (this, out0Id);
		tally_dyn_mem <GenericInterface> ("GenericInterface");
	};
	~TileInOut() override {
		delete in0;
		delete out0;
	};

};