# coding:utf-8
"""
Class for benchmarking of jpscore
See template_test/How_to_make_new_test.txt
"""

import fnmatch
import glob
import logging
from os import path
import os
from stat import S_ISREG, ST_MODE, ST_MTIME
import subprocess
import sys


__author__ = 'Oliver Schmidts'
__email__ = 'dev@jupedsim.org'
__credits__ = ['Oliver Schmidts', 'Mohcine Chraibi']
__copyright__ = '<2009-2015> Forschungszentrum Jülich GmbH. All rights reserved.'
__license__ = 'GNU Lesser General Public License'
__version__ = '0.1'
__status__ = 'Production'

def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

class JPSRunTestDriver(object):

    def __init__(self, testnumber, argv0, testdir, utestdir="..", jpsreportdir=".."):
        self.SUCCESS = 0
        self.FAILURE = 1
        # check if testnumber is digit
        assert isinstance(testnumber, float) or isinstance(testnumber, int), "argument <testnumber> is not digit"
        # only allow path and strings as path directory name
        assert isinstance(argv0, str), "argument <testdir> is not string"
        assert path.exists(testdir), "%s does not exist"%testdir
        assert path.exists(utestdir), "%s does not exist"%utestdir
        assert isinstance(argv0, str), "argument <argv0> is not string"
        assert path.exists(argv0), "%s is does not exist"%argv0
        self.testno = testnumber
        self.logfile = "log_test_%d.txt" % self.testno
        self.logfile = os.path.join(testdir, self.logfile)

        # touch file if not already there
        open(self.logfile, 'a').close()
        logging.basicConfig(filename=self.logfile, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.HOME = path.expanduser("~")
        self.DIR = testdir
        self.jpsreportdir = jpsreportdir # default is utestdir
        # Where to find the measured data from the simulations. We will use the Voronoi diagram
        # if testnumber == 100:
        #     self.simDataDir = os.path.join(self.DIR, "Output", "Fundamental_Diagram", "Individual_FD")
        # else:
        self.simDataDir = os.path.join(self.DIR, "Output", "Fundamental_Diagram", "Individual_FD")
        # Where to find the measured data from the experiments.
        # Assume that this directory is always data/
        self.expDataDir = os.path.join(self.DIR, "data")
        self.UTEST = utestdir
        self.CWD = os.getcwd()
        self.FILE = os.path.join(self.DIR, "master_ini.xml")

    def run_test(self, testfunction, fd=0, *args): #fd==1: make fundamental diagram
        assert hasattr(testfunction, '__call__'), "run_test: testfunction has no __call__ function"
        self.__configure()
        executable = self.__find_executable()
        results = []
        for inifile in self.inifiles:
            res = self.__execute_test(executable, inifile, testfunction, *args)
            results.append(res)

        if fd:
            from shutil import rmtree
            print "simDir", self.simDataDir
            print "sexpDir", self.expDataDir
            if os.path.exists(self.simDataDir):
                rmtree(self.simDataDir)

            jpsreport_exe = self.__find_jpsreport_executable()
            subprocess.call([jpsreport_exe, "%s" % self.jpsreport_ini])
            fd_exp, fd_sim = self.__compare_FD() #
            results = []
            results.append(fd_exp)
            results.append(fd_sim)
        return results

    def __compare_FD(self):
        import numpy as np
        experimenal_dir = self.expDataDir
        simulation_dir = self.simDataDir
        expfiles = glob.glob(os.path.join(experimenal_dir, "*.dat"))
        simfiles = glob.glob(os.path.join(simulation_dir, "*.dat"))
        if len(expfiles) == 0: # maybe we have txt files?
            expfiles = glob.glob(os.path.join(experimenal_dir, "*.txt"))
            if len(expfiles) == 0:
                logging.critical("compare_FD: no experimental data")
                exit(self.FAILURE)
        if len(simfiles) == 0:
            logging.critical("compare_FD: no simulation data")
            exit(self.FAILURE)


        once = 1
        for f in expfiles:
            if once:
                fd_exp = np.loadtxt(f)
                once = 0
            else:
                d = np.loadtxt(f)
                fd_exp = np.vstack((fd_exp, d))

        once = 1
        for f in simfiles:
            if once:
                fd_sim = np.loadtxt(f)
                if fd_sim.size == 0:
                    logging.critical("velocity, density data empty in <%s>", f)
                    exit(self.FAILURE)
                once = 0
            else:
                d = np.loadtxt(f)
                if d.size == 0:
                    logging.critical("velocity, density data empty in <%s>", f)
                    exit(self.FAILURE)
                fd_sim = np.vstack((fd_sim, d))

        return fd_exp, fd_sim

    def __configure(self):
        if self.CWD != self.DIR:
            logging.info("working dir is %s. Change to %s", os.getcwd(), self.DIR)
            os.chdir(self.DIR)
        logging.info("change directory to utest=%s", self.UTEST)
        os.chdir(self.UTEST)
        # -------- get directory of the code TRUNK
        # *** Note: assume that UTEST is always a direct subdirectory of TRUNK ***
        self.trunk = os.path.dirname(os.getcwd())
        logging.info("call makeini.py with -f %s", self.FILE)
        subprocess.call(["python", "makeini.py", "-f", "%s" % self.FILE])
        # os.chdir(self.DIR)
        logging.info("change directory back to %s", self.DIR)
        os.chdir(self.DIR)
        if self.UTEST == "..":
            lib_path = os.path.abspath(os.path.join(self.trunk, "Utest"))
        else:
            lib_path = os.path.abspath(self.UTEST)

        sys.path.append(lib_path)
        # initialise the inputfiles for jpscore
        self.geofile = os.path.join(self.DIR, "geometry.xml")
        self.inifiles = glob.glob(os.path.join("inifiles", "*.xml"))
        self.jpsreport_ini = os.path.join(self.DIR, "jpsreport_ini.xml")
        # if not path.exists(self.jpsreport_ini):
        #     logging.critical("jpsreport_ini <%s> does not exist", self.jpsreport_ini)
        #     exit(self.FAILURE)
        if not path.exists(self.geofile):
            logging.critical("geofile <%s> does not exist", self.geofile)
            exit(self.FAILURE)
        for inifile in self.inifiles:
            if not path.exists(inifile):
                logging.critical("inifile <%s> does not exist", inifile)
                exit(self.FAILURE)
        return

    def __find_executable(self):
        executable = os.path.join(self.trunk, "bin", "jpscore")

        # fix for windows
        if not path.exists(executable):
            matches = []
            for root, dirname, filenames in os.walk(os.path.join(self.trunk, 'bin')):
                for filename in fnmatch.filter(filenames, 'jpscore.exe'):
                    matches.append(os.path.join(root, filename))
            if len(matches) == 0:
                logging.critical("executable <%s> or jpscore.exe does not exist yet.", executable)
                exit(self.FAILURE)
            elif len(matches) > 1:
                matches = ((os.stat(file_path), file_path) for file_path in matches)
                matches = ((stat[ST_MTIME], file_path)
                           for stat, file_path in matches if S_ISREG(stat[ST_MODE]))
                matches = sorted(matches)
            executable = matches[0]
        # end fix for windows

        return executable

    def __find_jpsreport_executable(self):
        executable = os.path.join(self.jpsreportdir, "bin", "jpsreport")

        # fix for windows
        if not path.exists(executable):
            matches = []
            for root, dirname, filenames in os.walk(os.path.join(self.trunk, 'bin')):
                for filename in fnmatch.filter(filenames, 'jpsreport.exe'):
                    matches.append(os.path.join(root, filename))
            if len(matches) == 0:
                logging.critical("executable <%s> or jpsreport.exe does not exist yet.", executable)
                exit(self.FAILURE)
            elif len(matches) > 1:
                matches = ((os.stat(file_path), file_path) for file_path in matches)
                matches = ((stat[ST_MTIME], file_path)
                           for stat, file_path in matches if S_ISREG(stat[ST_MODE]))
                matches = sorted(matches)
            executable = matches[0]
        # end fix for windows

        return executable

    def __execute_test(self, executable, inifile, testfunction, *args):
        cmd = "%s --inifile=%s"%(executable, inifile)
        logging.info('start simulating with exe=<%s>', cmd)
        subprocess.call([executable, "--inifile=%s" % inifile])
        logging.info('end simulation ...\n--------------\n')
        trajfile = os.path.join("trajectories", "traj" + inifile.split("ini")[2])
        logging.info('trajfile = <%s>', trajfile)
        if not path.exists(trajfile):
            logging.critical("trajfile <%s> does not exist", trajfile)
            exit(self.FAILURE)
        res = testfunction(inifile, trajfile, *args)
        return res







