(define (main)
  (with-purse-module complaining-keeper
   (lambda (purse? make-purse! purse-balance! purse-transfer!)
     ; XXX ok, we really need a new naming convention!
     ;  among other things

     (let ((make-purse     (make-asker make-purse!     'make-purse))
           (purse-balance  (make-asker purse-balance!  'get-balance))
           (purse-transfer (make-asker purse-transfer! 'transfer)))
       (let ((alice (make-purse 42))
             (bob   (make-purse 0)))
         (print (purse-transfer (list bob alice 10)))
         (print (purse-balance alice))
         (print (purse-balance bob))
         (print (purse-transfer (list bob alice 100))))))))

(define (with-purse-module keeper f)
  (mlet ((seal unseal purse?) (make-sealer 'purse))
    (local

     ((define (purse-maker-server ? !)
        (let loop ()
          (mcase (?)
            (('make-purse arg k)
             (cond ((not (number? arg)) (k 'bad-type))
                   ((< arg 0) (k 'negative-amount))
                   (else 
                    (k (seal (sprout-spawn keeper
                                           (make-purse-server arg))))))
             (loop)))))

      (define (make-purse-server initial-amount)
        (lambda (? !)
          (let loop ((balance initial-amount))
            (mcase (?)
              (('get-balance _ k)
               (k balance)
               (loop balance))
              (('add arg k)
               (let ((new-balance (+ balance arg)))
                 (cond ((< new-balance 0)
                        (k 'insufficient-funds)
                        (loop balance))
                       (else
                        (k 'ok)
                        (loop new-balance)))))))))

      (define (purse-balance-server ? !)
        (let loop ()
          (mcase (?)
            (('get-balance arg k)
             ((unseal arg) (list 'get-balance #f k))
             (loop)))))

      (define (purse-transfer-server ? !)
        (let loop ()
          (mcase (?)
            (('transfer (to-purse/sealed from-purse/sealed amount) k)
             (let ((to-purse   (unseal to-purse/sealed))
                   (from-purse (unseal from-purse/sealed)))
               (if (< amount 0) 
                   (k 'negative-amount)
                   (let ((plaint (ask from-purse 'add (- amount))))
                     (if (not (equal? 'ok plaint))
                         (k plaint)
                         (to-purse (list 'add amount k))))))
             (loop))))))

     (f purse?
        (sprout-spawn keeper purse-maker-server)
        (sprout-spawn keeper purse-balance-server)
        (sprout-spawn keeper purse-transfer-server)))))

(define (sprout-spawn keeper fn)
  (mlet ((initial-? initial-!) (sprout))
    (spawn keeper (lambda ()
                    (mlet ((? !) (sprout))
                      (initial-! !)
                      (fn ? !))))
    (initial-?)))

(define (make-asker server! tag)
  (lambda (message)
    (ask server! tag message)))

(define (ask server! tag message)
  (mlet ((? !) (sprout))
    (server! (list tag message !))
    (?)))
