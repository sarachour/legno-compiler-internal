
stmts = []
def enq(st):
  stmts.append(st)

row = {}
for chipno in range(0,2):
  row['chip'] = chipno
  for tileno in range(0,4):
    row['tile'] = tileno
    for sliceno in range(0,4):
      row['slice'] = sliceno
      enq("calibrate {chip} {tile} {slice}".format(**row))
      break;

      # generate fanouts
      templ = "get_codes fanout {chip} {tile} {slice} {index} port {portid} output {range}"
      for indexno in range(0,2):
        row['index'] = indexno
        for portno in range(0,3):
          row['portid'] = portno
          for rng in ['m','h']:
            row['range'] = rng
            enq(templ.format(**row))

      # generate multipliers
      templ = "get_codes mult {chip} {tile} {slice} {index} port {portid} {port_type} {range}"

      for indexno in range(0,2):
        row['index'] = indexno
        row['port_type'] = 'input'
        for portno in range(0,2):
          row['portid'] = portno
          for rng in ['l','m','h']:
            row['range'] = rng
            enq(templ.format(**row))

        row['port_type'] = 'output'
        for portno in [0]:
          row['portid'] = portno
          for rng in ['l','m','h']:
            row['range'] = rng
            enq(templ.format(**row))

      templ = "get_codes integ {chip} {tile} {slice} {port_type} {range}"
      for typ in ['input', 'output']:
        row['port_type'] = typ
        for rng in ['l','m','h']:
          row['range'] = rng
          enq(templ.format(**row))

      # generate dac
      templ = "get_codes dac {chip} {tile} {slice} output {range}"
      for rng in ['m','h']:
        row['range'] = rng
        enq(templ.format(**row))


      if sliceno in [0,2]:
        templ = "get_codes adc {chip} {tile} {slice} input {range}"
        for rng in ['m','h']:
          row['range'] = rng
          enq(templ.format(**row))


with open('test_chip.grendel','w') as fh:
  for st in stmts:
    fh.write("%s\n" % st)
