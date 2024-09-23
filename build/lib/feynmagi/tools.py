tools = { 
'google' : 'google\ne.g google : "query" : "query_to_search_on_google_home_page"\nsearch on google home page',
'weblinks' : 'weblinks\ne.g weblinks : "query" : "query to search the relevent links from google\ngather links for related query',
'scrap' : 'scrap\ne.g scrap : "url" : "http://arxiv.org/id_papaer"\nDownload the page content and return a summary.',
'write_to_file' : 'write_to_file\ne.g write_to_file : "file_path": "<file_path>", "text": "<text to write to file>"\nwrite information to a file',
'read_file' : 'read_file\ne.g read_file : "file_path": "<file_path>", "page" : "page number (Optional)"\nRead and return file content page by page, e.g the dowloaded html pages',
'append_to_file' : 'append_to_file\ne.g append_to_file : "file_path": "<file_path>", "text": "<text to write to file>"\nwrite information to a file',
'display_file' : 'display_file\ne.g display-file : "file_path" : "path _to_file"\ndisplay the content of a file to user output',
'dev_code' : 'dev_code\ne.g dev-code : "objective" : "objective of the code", "language": "language", "framework": "<framework>", "file_name" : "<file_name>" \nenerate simple module code to achieve an elementary task',
'execute_code' : 'execute_code\ne.g execute-code :  "file_name" : "<file_name>", "input": "<input data>", "environment": "<environment>"\nexcute code in file',
'calculate' : 'calculate\ne.g. calculate: 4 * 7 / 3\nRuns a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary',
'email' : 'email\ne.g email : "to" : "user@domain.com", "subject" : "subject", "body" : "html code only for body content", "attachment" : "(optional) path to file"\nSend an email',
'call_agent' : 'call_agent\ne.g call_agent : "agent" : "agent_name", "context" : "input to pass to agent" \nCall a given agent with output context'   
}