import logging
import requests
import hashlib
from BeautifulSoup import BeautifulSoup as soup

from urlparse import urlparse

import time
import os
import json
import config

allowed_netlocs = ['4048.co.nf','3301.co.nf','4048712.co.nf','52.32.251.99']
def main():

    urls = load_urls()
    state = load_state()
    i = 0
    while i < len(urls):
        url = urls[i]
        if isinstance(url, basestring):
            url = {
                'url': url,
                'type': 'html',
                'referer': url,
            }
            urls[i] = url
        i += 1
        try:
            body,hash = get(url)
        except Exception as e:
            continue

        if url['url'] not in state:
            state[url['url']] = {
                'previous_hash': None,
                'permutations': 0,
            }

        if hash != state[url['url']]['previous_hash']:
            state[url['url']]['previous_hash'] = hash
            state[url['url']]['permutations'] = state[url['url']]['permutations'] + 1
            print "Permutation %s: %s was updated on %s" % (state[url['url']]['permutations'],url['url'], time.ctime())
            store_body(url,body)
            if url['type'] == 'img':
                send_mail(config.email,'Updated image url %s' % url['url'],'Not sending the image, lolz')
                continue
            else:
                send_mail(config.email,'Updated site url %s' % url['url'],body)
            try:
                s = soup(body)
                for anchor in s('a'):
                    try:
                        new_url = {
                            'url': get_url(url['url'],anchor['href']),
                            'type':'html',
                            'referer':url['referer']
                        }
                        if new_url not in urls:
                            print "Permutation %s: Found URL in %s. New URL: %s" % (state[url['url']]['permutations'],url['url'], new_url['url'])
                            urls.append(new_url)
                            send_mail(config.email,'Found new website %s' % new_url['url'],'Hoi')
                            # Send e-mail
                    except Exception as e:
                        print e
                for img in s('img'):
                    try:
                        new_url = {
                            'url': get_url(url['url'],img['src']),
                            'type':'img',
                            'referer':url['referer']
                        }
                        if new_url not in urls:
                            print "Permutation %s: Found URL in %s. New URL: %s" % (state[url['url']]['permutations'],url['url'], new_url['url'])
                            urls.append(new_url)
                            send_mail(config.email,'Found new image %s' % new_url['url'],'Hoi')
                    except Exception as e:
                        print e
            except Exception as e:
                continue

    store_urls(urls)
    store_state(state)


def store_body(url,body,type='txt'):
    if url['type'] == 'img':
        type = url['url'].split('.')[-1]
    with open('out/%s_%s.%s' % (url['url'].replace('/','_'), time.time(),type),'w') as f:
        f.write(body)

def get_url(base, new):
    result_base =  urlparse(base)
    result_new = urlparse(new)
    scheme = result_new.scheme if result_new.scheme != '' else result_base.scheme
    netloc = result_new.netloc if result_new.netloc != '' else result_base.netloc
    path_b = result_base.path
    path_n = result_new.path
    if len(path_n) > 0 and path_n[0] == '/':
        # Absolute path, so use it
        path = path_n
    elif len(path_n) > 0:
        if  len(path_b) > 0 and path_b[0] == '/':
            # absolute base path, so take off everything after last /
            path = '/'.join(path_b.split('/')[0:-1]) + path_n
        else:
            path = path_n
    out = scheme + "://" + netloc + '/' + path
    if netloc not in allowed_netlocs:
        raise Exception("Found URL to unallowed domain %s" % out)
    return scheme + "://" + netloc + '/' + path

def load_state():
    try:
        with open('state.json') as f:
            return json.loads(f.read())
    except:
        return {}
def store_state(state):
    with open('state.json','w') as f:
        f.write(json.dumps(state, indent=4, sort_keys=True))
    pass

def get(url):
    headers = {
        'Pragma':'no-cache',
        'DNT':'1',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'en-US,en;q=0.8',
        'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36',
        'Referer': url['referer'],
        'Connection':'keep-alive',
        'Cache-Control':'no-cache',
    }
    if url['type'] == 'html':
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    elif url['type'] == 'img':
        headers['Accept'] = 'image/webp,image/*,*/*;q=0.8'

    response = requests.get(url['url'],headers=headers)
    body = response.content
    hash = hashlib.md5(body).hexdigest()
    return body, hash

def load_urls():
    with open('urls.json') as f:
        return json.loads(f.read())

def store_urls(urls):
    with open('urls.json','w') as f:
        f.write(json.dumps(urls, indent=4, sort_keys=True))

def send_mail(address, title, body):
    import sendgrid

    sg = sendgrid.SendGridClient(config.api_key)

    message = sendgrid.Mail()
    message.add_to(config.email)
    message.set_subject(title)
    message.set_text(body)
    message.set_from('Cicada <cicada@email.com>')
    status, msg = sg.send(message)
    pass

if __name__ == '__main__':
    print "Scraping started"
    while True:
        main()
        time.sleep(30)