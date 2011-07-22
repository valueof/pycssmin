import os
from cssmin import cssmin

def main():
    files = os.listdir('./tests')
    files = [ f for f in files if f.endswith('.css') ]
    failed = False

    for f in files:
        orig = ''
        targ = ''

        with open(os.path.join('./tests', f), 'r') as stream:
            orig = stream.read()

        with open(os.path.join('./tests', f + '.min'), 'r') as stream:
            targ = stream.read()

        if cssmin(orig) != targ:
            failed = True
            print 'failure: ', f

    if not failed:
        print 'All tests passed'

if __name__ == '__main__':
    main()
