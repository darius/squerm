(define (main)
  (mlet ((purse? make-purse! purse-balance! purse-transfer!)
         (make-purse-module complaining-keeper))
    ;; XXX ok, we really need a new naming convention!
    ;;  among other things

    (let ((make-purse     (make-asker make-purse!     'make-purse))
          (purse-balance  (make-asker purse-balance!  'get-balance))
          (purse-transfer (make-asker purse-transfer! 'transfer)))
      (let ((alice (make-purse 42))
            (bob   (make-purse 0)))
        (print (purse-transfer (list bob alice 10)))
        (print (purse-balance alice))
        (print (purse-balance bob))
        (print (purse-transfer (list bob alice 100)))))))

(define (make-purse-module keeper)
  (mlet ((seal unseal purse?) (make-sealer 'purse))
    (local

     ((define (purse-maker-server ? !)
        (let loop ()
          (mcase (?)
            (('make-purse initial-amount k)
             (cond ((not (number? initial-amount)) (k 'bad-type))
                   ((< initial-amount 0) (k 'negative-amount))
                   (else 
                    (k (seal (sprout-spawn keeper
                                           (make-purse-server initial-amount))))))
             (loop)))))

      (define (make-purse-server initial-amount)
        (lambda (? !)
          (let loop ((balance initial-amount))
            (mcase (?)
              (('get-balance _ k)
               (k balance)
               (loop balance))
              (('add amount k)
               (let ((new-balance (+ balance amount)))
                 (cond ((< new-balance 0)
                        (k 'insufficient-funds)
                        (loop balance))
                       (else
                        (k 'ok)
                        (loop new-balance)))))))))

      (define (purse-balance-server ? !)
        (let loop ()
          (mcase (?)
            (('get-balance purse/sealed k)
             ((unseal purse/sealed) (list 'get-balance #f k))
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

     (list purse?
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
