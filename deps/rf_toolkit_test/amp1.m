ckt = circuit();
amp_1 = rfckt.amplifier('NF',15,'OIP3',2);
amp_2 = rfckt.amplifier('NF',15,'OIP3',0.5);
ckt = rfckt.cascade('Ckts',{amp_1,amp_2})

freq = logspace(0,11,101)';
analyze(ckt,freq);
params = ckt.AnalyzedResult.S_Parameters;
noise = ckt.AnalyzedResult.NF;
delay = ckt.AnalyzedResult.GroupDelay;
return;
ref_imp = 50;
src_imp = 0;
load_imp = Inf;
method = 2;
tfckt = s2tf(params,ref_imp,src_imp,load_imp,method);
disp(noise);
disp(tfckt);
tffit = rationalfit(freq,tfckt)

sampleTime = 2e-6;
t = (0:10000)'*sampleTime;
input = sin(1000.0*t);

signal = timeresp(tffit, input, sampleTime);

figure
plot(t,input,t,signal,'LineWidth',2)
axis([0 max(t) -2.0 2.0])
title('Input-Output Relation For Cascaded Amplifiers')
xlabel('Time (sec)')
ylabel('Voltage (volts)')
legend('Vinput','V(AMP)','Location','NorthWest')
