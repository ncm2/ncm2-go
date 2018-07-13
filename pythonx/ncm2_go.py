# -*- coding: utf-8 -*-

import vim
from ncm2 import Ncm2Source, getLogger, Popen
import re
import os
import glob
import subprocess
from os import path
import json


logger = getLogger(__name__)

func_pat = re.compile(r'func\((.*?)\)')


class Source(Ncm2Source):

    def check(self):
        data = self.nvim.call('ncm2_go#data')
        if not self.get_gocode(data):
            self.nvim.call(
                'ncm2_go#error', 'Cannot find [gocode] executable. Please install gocode http://github.com/nsf/gocode')

    def get_gocode(self, data):
        from distutils.spawn import find_executable
        gocode = data['gocode_path']
        if 'GOPATH' in os.environ:
            res = path.join(os.environ['GOPATH'], 'bin', gocode)
            res = find_executable(res)
            if res:
                return res
        res = find_executable(gocode)
        return res

    def on_complete(self, ctx, data, lines):

        src = "\n".join(lines)
        src = self.get_src(src, ctx)
        lnum = ctx['lnum']
        ccol = ctx['ccol']
        bcol = ctx['bcol']
        typed = ctx['typed']
        filepath = ctx['filepath']
        startccol = ctx['startccol']

        src = src.encode('utf-8')
        offset = self.lccol2pos(lnum, ccol, src)

        gocode = self.get_gocode(data)
        args = args = [gocode, '-f', 'json',
                       'autocomplete', filepath, '%s' % offset]
        proc = subprocess.Popen(args=args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)

        result, errs = proc.communicate(src, timeout=10)
        logger.debug("args: %s, result: [%s]", args, result)

        # result: [1, [{"class": "func", "name": "Print", "type": "func(a ...interface{}) (n int, err error)"}, ...]]
        result = json.loads(result.decode())
        if not result:
            return

        completions = result[1]
        startbcol = bcol - result[0]
        startccol = len(typed.encode()[: startbcol-1]) + 1

        if startbcol == bcol and re.match(r'\w', ctx['typed'][-1]):
            # workaround gocode bug when completion is triggered in a
            # golang string
            return

        matches = []

        for complete in completions:

            # {
            #     "class": "func",
            #     "name": "Fprintln",
            #     "type": "func(w !io!io.Writer, a ...interface{}) (n int, err error)"
            # },
            item = dict(word=complete['name'],
                        icase=1,
                        dup=1,
                        menu=complete.get('type', ''),
                        user_data={}
                        )

            self.render_snippet(complete, item)

            matches.append(item)

        logger.info('startccol %s, matches %s', startccol, matches)
        self.complete(ctx, startccol, matches)

    def render_snippet(self, complete, item):

        # snippet support
        if complete.get('class', '') != 'func':
            return

        m = func_pat.search(complete.get('type', ''))
        if not m:
            return

        params = m.group(1)
        params = params.split(',')
        logger.info('snippet params: %s', params)
        snip_params = []
        num = 1
        optional = ''
        for param in params:
            param = param.strip()
            if not param:
                logger.error(
                    "failed to process snippet for item: %s, param: %s", item, param)
                break
            name = param.split(' ')[0]
            if param.find('...') >= 0:
                # optional args
                if num > 1:
                    optional += self.snippet_placeholder(
                        num, ', ' + name + '...')
                else:
                    optional += self.snippet_placeholder(num, name + '...')
                break
            snip_params.append(self.snippet_placeholder(num, name))
            num += 1

        ud = item['user_data']
        ud['is_snippet'] = 1
        ud['snippet'] = item['word'] + \
            '(' + ", ".join(snip_params) + optional + ')${0}'

    def snippet_placeholder(self, num, txt=''):
        txt = txt.replace('\\', '\\\\')
        txt = txt.replace('$', r'\$')
        txt = txt.replace('}', r'\}')
        if txt == '':
            return '${%s}' % num
        return '${%s:%s}' % (num, txt)


source = Source(vim)

on_complete = source.on_complete

source.check()
