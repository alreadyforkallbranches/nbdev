# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/14_test.ipynb.

# %% auto 0
__all__ = ['nbglob', 'HiddenPrints', 'test_nb', 'nbprocess_test']

# %% ../nbs/14_test.ipynb 2
from fastcore.all import *
from .read import *
import time
import os, sys
import traceback

# %% ../nbs/14_test.ipynb 4
def nbglob(fname=None, recursive=None, config_key='nbs_path') -> L:
    "Find all files in a directory matching an extension given a `config_key`."
    if recursive is None: recursive=get_config().get('recursive', 'False').lower() == 'true'
    fname = Path(fname or get_config().path(config_key))
    return globtastic(path=fname,recursive=recursive,file_glob='*.ipynb', skip_file_re='^[_.]', skip_folder_re='^[_.]')

# %% ../nbs/14_test.ipynb 5
_re_directives = re.compile(r'^\s*#\s*\|\s*(.*)', flags=re.MULTILINE)

# %% ../nbs/14_test.ipynb 7
def _is_intersect(l1, l2): return bool(set(L(l1)).intersection(set(L(l2))))

# %% ../nbs/14_test.ipynb 9
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

# %% ../nbs/14_test.ipynb 10
def test_nb(fn, skip_flags=None, force_flags=None):
    "Execute tests in notebook in `fn` except those with `skip_flags`"
    os.environ["IN_TEST"] = '1'
    flags=set(L(skip_flags)) - set(L(force_flags))
    rnr = NBRunner()
    print(f"testing {fn}")
    start = time.time()
    try:
        nb = read_nb(fn)
        nbcode = nb.cells.filter(lambda x: x.cell_type == 'code' and x.source)
        for cell in nbcode:
            directives = _re_directives.findall(cell.source)
            if not _is_intersect(flags, directives):
                with HiddenPrints():
                    rnr.run(cell)
        return True,time.time()-start
    except Exception as e:
        fence = '='*50
        print(f'\n\nError in {fn} when running cell:\n{fence}\n{cell.source}\n\n{type(e).__name__}: {e}\n{fence}')
        traceback.print_exc()
        return False,time.time()-start
    finally: 
        if "IN_TEST" in os.environ:
            os.environ.pop("IN_TEST")

# %% ../nbs/14_test.ipynb 15
@call_parse
def nbprocess_test(
    fname:str=None,  # A notebook name or glob to convert
    flags:str=None,  # Space separated list of test flags you want to run that are normally ignored
    n_workers:int=None,  # Number of workers to use
    timing:bool=False,  # Timing each notebook to see the ones are slow
    pause:float=0.5  # Pause time (in secs) between notebooks to avoid race conditions
):
    "Test in parallel the notebooks matching `fname`, passing along `flags`"
    skip_flags = get_config().get('tst_flags')
    skip_flags = (skip_flags.split() if skip_flags else []) + ['eval: false']
    force_flags = flags.split() if flags else []
    files = nbglob(fname)
    files = [Path(f).absolute() for f in sorted(files)]
    assert len(files) > 0, "No files to test found."
    if n_workers is None: n_workers = 0 if len(files)==1 else min(num_cpus(), 8)
    # make sure we are inside the notebook folder of the project
    os.chdir(get_config().path("nbs_path"))
    results = parallel(test_nb, files, skip_flags=skip_flags, force_flags=force_flags, n_workers=n_workers, pause=pause)
    passed,times = [r[0] for r in results],[r[1] for r in results]
    if all(passed): print("All tests are passing!")
    else:
        msg = "The following notebooks failed:\n"
        raise Exception(msg + '\n'.join([f.name for p,f in zip(passed,files) if not p]))
    if timing:
        for i,t in sorted(enumerate(times), key=lambda o:o[1], reverse=True):
            print(f"Notebook {files[i].name} took {int(t)} seconds")