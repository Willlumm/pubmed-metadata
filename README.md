# PubMed Metadata
This was a project I worked on during an internship at Frontiers Media in 2019.
Beware, it predates my awareness of python conventions and libraries such as pandas.
Original README below:

~~~~~~~~ extractPubMed Documentation ~~~~~~~~

Downloading PubMed XML files by query:
	This is the easiest and most customisable way of downloading PubMed publication metadata.
	1) Go to the PubMed Advanced Search Builder page at https://www.ncbi.nlm.nih.gov/pubmed/advanced.
	2) Click "Edit" and enter your query into the text box. Then click "Search" to go to the Search Results page.
	4) Click "Send to", select "File", and change "Format" to XML. Then click "Create File", and the results will download as an XML file.
	
Query details:
	The following query was used to find the most relevant types of publications since 2017:
		(Case Reports[ptyp] OR Clinical Trial[ptyp] OR Journal Article[ptyp] OR Review[ptyp] OR systematic[sb] OR Technical Report[ptyp]) NOT (Editorial[ptyp] OR Biography[ptyp] OR Autobiography[ptyp]) AND ("2017/01/01"[EPDAT] : "2017/03/31"[EPDAT])
	Useful tags:
		[TA] 	= Journal 						= filter by a journal title, title abbreviation, or ISSN.
		[MH] 	= MeSH Terms					= filter by terms found in the NLM Medical Subject Headings.
		[JID]	= NLM ID						= filter by a journal NLM ID.
		[OT]	= Other Term					= filter by terms found in the author keyword field.
		[PL]	= Publication Place				= filter by journal's country.
		[DP]	= Publication Date				= filter by range of publication dates.
		[EPDAT]	= Electronic Publication Date 	= filter by range of online publication dates.
		[PT]	= Publication Type				= filter by type of publications. The most relevant types are "Journal Article", "Case Report", "Clinical Trial", "Review", and "Technical Report", but it also worth filtering by unwanted types such as "Biography" or "Editorial". The full list of types can be found at https://www.ncbi.nlm.nih.gov/books/NBK3827/table/pubmedhelp.T.publication_types/?report=objectonly
		[SB] 	= Subset						= can be used to filter by subject or journal category. Systemic reviews fall under this tag.
		[TW] 	= Text Words					= filter by words in the publication title, abstract, MeSH terms, publication types, and other terms.
		[TI]	= Title							= filter by words in the publication title.
		[TIAB]	= Title/Abstract				= filter by words in the publication title or abstract.
	The full list of tags can be found at https://www.ncbi.nlm.nih.gov/books/NBK3827/
	These tags can be combined using the operators AND, OR, NOT to create more complex searches.
	To search between a range of dates, use ":" in between the start and end date.

Downloading PubMed XML files in bulk:
	This method allows the full collection of PubMed publication metadata to be downloaded quickly, but cannot be queried.
	1) Go to the PubMed 2019 baseline files at ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline.
	2) Download the desired XML files. The files contain the publications approximately in order by date, but are not labelled.
	3) If you want files updated since the beginning of 2019, go to ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles and repeat step 2.
	
Data Processing:
	1) Read the XML file or each XML file in a folder and store the data for each publication as a dictionary. All the publication dictionaries are stored in a list.
	[{fields : values}]
	2) Write the publications output file from this list of publication data.
	3) Sort the publications into lists by NLM ID and store the lists in a dictionary. Each key in the dictionary is an NLM ID, and each value in the dictionary is a list of publication dictionaries with the corresponding NLM ID.
	{NLM IDs : [{fields : values}]}
	4) Sort each list in the NLM ID dictionary by the time period (year, quarter, or month).
	{NLM IDs : {time periods : [{fields : values}]}}
	5) Get the interval lists for each list of publication dictionaries and make the calculations on the interval lists.
	{NLM IDs : {time periods : {intervals : {Calculations : values}}}}
	6) Write the dates output file from this nested dictionary.
	
Publications Output File:
	The publications output CSV file is a list of all the extracted metadata by publication. If a field is not found in the XML file, the entry will be blank in the CSV file. If attempting to write more than 750,000 publications, it will split the publications into seperate files by year, quarter, or month.
	Columns:
		PMID				= PubMed Identification. This is the only field every publication is guaranteed to have.
		DOI 				= Digital Object Identification of the publication.
		Publication Types 	= list of publication types associated with the publication.
		Journal				= journal name.
		ISSN				= International Standard Serial Number of the journal.
		ISSN-L				= ISSN-Linking of the journal.
		NLM ID				= National Library of Medicine Identification of the journal.
		Date Received		= date publication was received by the journal from the author.
		Date Revised		= date revisions to the publication were submitted. Typically, fewer publications have this date.
		Date Accepted		= date journal accepted the paper for publication.
		Date Online			= date paper was published online.
		
Dates Output File:
	The dates output CSV file is a list of calculations on intervals between metadata dates by journal NLM ID and time period in which the publications were published online.
	Columns:
		NLM ID			= National Library of Medicine Identification of the journal.
		Time Period 	= time period in which the publications were published online. Can be configured by year, quarter, or month.
		Date Intervals	= number of days between each metadata date. There are six possible intervals between each metadata date; received-revised, received-accepted, received-online, revised-accepted, revised-online, and accepted-online.
		Calculations	= for each interval, five calculations were made; count, mean, first quartile, median, third quartile. The calculations only include publications with two valid appropriate dates and an interval between 0 and 1461 days.
		Aggregate		= counts of; the number of valid publications for each metadata date, total number of publications regardless of validity, total number of publications with valid data.
