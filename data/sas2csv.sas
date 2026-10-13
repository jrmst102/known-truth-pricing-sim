SV%let path=C:\Data;
libname dff v6 "&path";

%macro sas2csv/parmbuff;
	%let num=1;
	%let dsname=%scan(&syspbuff,&num);
	%do %while(&dsname ne);
		proc export data=dff.&dsname
			outfile="&path\&dsname..csv"
			dbms=csv
			replace;
		run;
		%let num=%eval(&num+1);
		%let dsname=%scan(&syspbuff,&num);
	%end;
%mend sas2csv;

%sas2csv(upcana,upcbat,upcber,upcbjc,upccer,upcche,upccig,upccoo,upccra,upccso,upcdid,upcfec,upcfrd,upcfre,upcfrj,upcfsf,upcgro,upclnd,upcoat,upcptw,upcrfj,upcsdr,upcsha,upcsna,upcsoa,upctbr,upctna,upctpa,upctti)

%sas2csv(wana,wbat,wber,wbjc,wcer,wche,wcig,wcoo,wcra,wcso,wdid,wfec,wfrd,wfre,wfrj,wfsf,wgro,wlnd,woat,wptw,wrfj,wsdr,wsha,wsna,wsoa,wtbr,wtna,wtpa,wtti)