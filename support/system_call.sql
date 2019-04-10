
CREATE FUNCTION system_call (txt text)
  RETURNS int
AS $$
   from subprocess import Popen
   return Popen(txt, shell=True).wait()
$$ LANGUAGE plpython3u;
